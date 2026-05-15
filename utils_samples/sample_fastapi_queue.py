import sys
import uuid
from typing import Any
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from app.utils.log_utils.trace_log import TraceLog
from fastapi.responses import JSONResponse
from starlette.types import ASGIApp, Scope, Receive, Send

# Queue版ロガー。log_file を直接指定。
logger = TraceLog(log_file="fastapi_queue.log", service_name="fastapi-app")

@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    logger.shutdown()

class TraceLoggingMiddleware:
    """BaseHTTPMiddlewareを避けた、高速な ASGI ミドルウェア"""
    def __init__(self, app: ASGIApp):
        self.app = app

    async def __call__(self, scope: Scope, receive: Receive, send: Send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # 1. 計測開始
        logger.start(request_id, {"method": scope["method"], "path": scope["path"]})

        status_code = [0]

        async def wrapped_send(message: Any) -> None:
            if message["type"] == "http.response.start":
                status_code[0] = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, wrapped_send)
            # 正常終了時（アプリが 404 や 500 を返した場合もここを通る）
            final_status = status_code[0] or 200
            level = "error" if final_status >= 500 else "info"
            logger.end({"status": final_status}, level=level)

        except Exception as e:
            # 未捕捉の例外発生時
            logger.end(data={"path": scope["path"]}, event_message="request_exception", level="error", exc_info=e)

            # すでにレスポンスが開始（sendが呼ばれている）されていない場合のみ、500レスポンスを返却
            if status_code[0] == 0:
                res = JSONResponse(status_code=500, content={"message": "Internal Server Error"})
                await res(scope, receive, send)
            raise e

        finally:
            # 保険：何らかの理由で logger.end が呼ばれなかった場合のメモリリーク防止
            logger._start_times.pop(request_id, None)

app = FastAPI(lifespan=lifespan)
app.add_middleware(TraceLoggingMiddleware)

@app.get("/")
async def index():
    logger.info({"msg": "Hello from Queue Logger"})
    return {"message": "ok"}

@app.get("/error")
async def trigger_error():
    # スタックトレースのテスト
    raise ValueError("FastAPI Queue Error Test")

# グローバル例外ハンドラを追加して、Uvicornへの例外伝播を止める
@app.exception_handler(Exception)
async def custom_exception_handler(request: Request, exc: Exception):
    # ここで例外を捕捉し、適切なレスポンスを返すことで、Uvicornのデフォルトエラー出力を抑制します。
    # ミドルウェアで既にログは記録されているため、ここではログは出力しません。
    return JSONResponse(
        status_code=500,
        content={"message": "Internal Server Error", "detail": str(exc)}
    )