import uuid
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.utils.log_utils.trace_log import TraceLog

# グローバルにロガーを定義（実際のパスやサービス名に合わせる）
logger = TraceLog(log_file="fastapi-app.log")

@asynccontextmanager
async def lifespan(app: FastAPI):
    # アプリ起動時の処理（必要に応じて）
    yield
    # アプリ終了時に確実にシャットダウン（ソケットのクローズ等）
    logger.shutdown()

class TraceLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # 1. Request ID の生成（ヘッダーにあればそれを使う運用も一般的）
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        
        # 2. 計測開始 (ContextVar に保存される)
        logger.start(request_id, {"method": request.method, "path": request.url.path})
        
        try:
            response = await call_next(request)
            
            # 3. 計測終了 (経過時間が自動計算される)
            logger.end({"status_code": response.status_code})
            return response
            
        except Exception as e:
            # 4. エラーログ出力 (例外オブジェクトを直接渡す)
            logger.error(
                event_message="Request Processing Failed",
                exc_info=e,
                data={"path": request.url.path}
            )
            raise e

app = FastAPI(lifespan=lifespan)
app.add_middleware(TraceLoggingMiddleware)

@app.get("/")
async def index():
    # ミドルウェアで start 済みなので、ここでは引数なしで呼べる
    logger.info({"msg": "Hello from Controller"})
    return {"message": "ok"}

@app.get("/error")
async def trigger_error():
    raise ValueError("Something went wrong!")