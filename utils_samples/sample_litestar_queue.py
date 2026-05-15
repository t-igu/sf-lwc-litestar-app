import sys
import uuid
from typing import Any
from litestar import Litestar, get, Request
from litestar.middleware import AbstractMiddleware
from app.utils.log_utils.trace_log import TraceLog

# Queue版ロガー
logger = TraceLog(log_file="litestar_queue.log", service_name="litestar-app")

class LoggingMiddleware(AbstractMiddleware):
    async def __call__(self, scope: Any, receive: Any, send: Any) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        request = Request(scope)
        request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
        logger.start(request_id, {"method": request.method, "path": request.url.path})

        status_code = [0]

        async def wrapped_send(message: Any) -> None:
            if message["type"] == "http.response.start":
                status_code[0] = message["status"]
            await send(message)

        try:
            await self.app(scope, receive, wrapped_send)
            # 正常終了時 (Litestarがエラーをトラップして500を返した場合を含む)
            final_status = status_code[0] or 200
            level = "error" if final_status >= 500 else "info"
            logger.end(data={"status": final_status}, level=level)

        except Exception as e:
            # 未捕捉の例外発生時
            logger.end(data={"path": request.url.path}, level="error", exc_info=e)
            raise e
        finally:
            # 保険：メモリリーク防止
            logger._start_times.pop(request_id, None)
@get("/")
async def index() -> dict:
    logger.debug({"detail": "Using Queue Logger"})
    return {"status": "ok"}

@get("/error")
async def trigger_error() -> None:
    raise RuntimeError("Litestar Queue Error Test")

app = Litestar(
    route_handlers=[index, trigger_error],
    middleware=[LoggingMiddleware],
    on_shutdown=[logger.shutdown]
)