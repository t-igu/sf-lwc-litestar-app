import uuid
from typing import Any
from litestar import Litestar, get, Request, Response
from litestar.middleware import AbstractMiddleware
from app.utils.log_utils.trace_log import TraceLog

# ロガーの初期化
logger = TraceLog(log_file="litestar_queue.log", service_name="litestar-app")

class LoggingMiddleware(AbstractMiddleware):
    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        # HTTP リクエスト以外（WebSocketなど）はスキップ
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        # 1. Request ID の生成
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))

        # 2. 計測開始
        logger.start(request_id, {"method": scope["method"], "path": scope["path"]})

        status_code = [0]  # 未設定状態

        async def wrapped_send(message: Any) -> None:
            if message["type"] == "http.response.start":
                status_code[0] = message["status"]
            await send(message)

        try:
            # 次のハンドラーまたはミドルウェアを実行
            await self.app(scope, receive, wrapped_send)
            # 正常終了時 (Litestar 内部で 404 や 500 が処理された場合を含む)
            final_status = status_code[0] or 200
            level = "error" if final_status >= 500 else "info"
            logger.end(data={"status": final_status}, level=level)

        except Exception as e:
            # 未捕捉の例外発生時
            logger.end(data={"path": scope["path"]}, event_message="request_exception", level="error", exc_info=e)

            # すでにレスポンスが開始されていない場合のみ、500レスポンスを返却して ASGI サーバーへの伝播を止める
            if status_code[0] == 0:
                res = Response(status_code=500, content={"message": "Internal Server Error"})
                await res(scope, receive, send)
            raise e
        finally:
            # 保険：メモリリーク防止
            logger._start_times.pop(request_id, None)

def custom_exception_handler(request: Request, exc: Exception) -> Response:
    # Uvicorn への例外伝播を抑制するためのハンドラ
    return Response(
        status_code=500,
        content={"message": "Internal Server Error", "detail": str(exc)}
    )

@get("/")
async def index() -> dict:
    logger.debug({"detail": "Processing in Litestar"})
    return {"status": "ok"}

@get("/error")
async def trigger_error() -> None:
    raise RuntimeError("Litestar Exception")

app = Litestar(
    route_handlers=[index, trigger_error],
    middleware=[LoggingMiddleware],
    on_shutdown=[logger.shutdown],
    exception_handlers={Exception: custom_exception_handler}
)

# ※ 実際の運用では lifespan を使う構成も可能です