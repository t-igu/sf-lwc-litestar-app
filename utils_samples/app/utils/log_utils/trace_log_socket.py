import importlib
import logging
import socket
import os
import sys
import time
from typing import Any, Optional

import msgspec
import structlog
from structlog.types import Processor, EventDict

TRACE_LEVEL_NUM = 5

# structlog 内部マッピングの拡張
try:
    _sn = importlib.import_module("structlog._native")
    getattr(_sn, "LEVEL_TO_NAME")[TRACE_LEVEL_NUM] = "trace"
    getattr(_sn, "NAME_TO_LEVEL")["trace"] = TRACE_LEVEL_NUM
except (ImportError, AttributeError, TypeError):
    pass

logging.addLevelName(TRACE_LEVEL_NUM, "TRACE")

def _convert_data(data: Any) -> Any:
    if data is None: return {}
    if isinstance(data, dict): return data
    try:
        return msgspec.to_builtins(data)
    except Exception:
        return str(data)

class TraceLog:
    """
    複数アプリ対応・超高速非同期ロガー。
    ログデータを Unixドメインソケット経由でデーモンへ送信する。
    """
    _STR_TO_LEVEL = {
        "trace": TRACE_LEVEL_NUM,
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
    }

    def __init__(self, service_name: str = "app", socket_path: str = "/tmp/tracelog.sock"):
        self._service_name = service_name
        self._socket_path = socket_path
        self._start_times: dict[str, float] = {}
        self._encoder = msgspec.json.Encoder()

        # ソケットの初期化
        self._sock = None # Initialize to None
        try:
            self._sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
            # 非ブロッキングモードに設定し、デーモンが居なくてもアプリを止めない
            self._sock.setblocking(False)
        except Exception as e:
            print(f"TraceLog Client Init Error: {e}", file=sys.stderr)
            # If socket creation fails, _sock remains None.

        self._setup_structlog()
        self._logger = structlog.get_logger()
        self._integrate_standard_logging()

    def _setup_structlog(self):
        processors: list[Processor] = [
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            self._socket_processor,
        ]
        structlog.configure(
            processors=processors,
            logger_factory=structlog.PrintLoggerFactory(),
            cache_logger_on_first_use=True,
        )

    def _socket_processor(self, logger: Any, method_name: str, event_dict: EventDict) -> Any:
        event_dict["service"] = self._service_name
        if not self._sock: # If socket failed to initialize, drop the log
            raise structlog.DropEvent
        try:
            payload = self._encoder.encode(event_dict)
            # デーモンへ送信 (コネクションレスなので高速)
            self._sock.sendto(payload, self._socket_path)
        except (BlockingIOError, socket.error) as e:
            # デーモン未起動またはバッファフル時はドロップ。デバッグ用にエラーを出力
            print(f"TraceLog Client: Log dropped due to socket error: {e}", file=sys.stderr)
        raise structlog.DropEvent

    def _integrate_standard_logging(self):
        class InterceptHandler(logging.Handler):
            def emit(self, record):
                level = record.levelno
                event_message = record.getMessage()
                kwargs = {
                    "logger_name": record.name,
                    "process_id": record.process,
                    "thread_name": record.threadName,
                }
                if record.exc_info:
                    kwargs["exc_info"] = record.exc_info
                structlog.get_logger("stdlib").log(level, event_message, **kwargs)

        root_logger = logging.getLogger()
        for h in root_logger.handlers[:]:
            root_logger.removeHandler(h)
        root_logger.addHandler(InterceptHandler())
        root_logger.setLevel(TRACE_LEVEL_NUM)

    def _log(self, level: str, request_id: str, data: Any, event_message: Optional[str] = None, **kwargs):
        level_int = self._STR_TO_LEVEL.get(level.lower(), logging.INFO)
        self._logger.log(level_int, event_message or request_id, request_id=request_id, data=_convert_data(data), **kwargs)

    def debug(self, request_id: str, data: Any = None, event_message: Optional[str] = None):
        self._log("debug", request_id, data, event_message=event_message)

    def trace(self, request_id: str, data: Any = None, event_message: Optional[str] = None):
        self._log("trace", request_id, data, event_message=event_message)

    def info(self, request_id: str, data: Any = None, event_message: Optional[str] = None):
        self._log("info", request_id, data, event_message=event_message)

    def warning(self, request_id: str, data: Any = None, event_message: Optional[str] = None):
        self._log("warning", request_id, data, event_message=event_message)

    def error(self, request_id: str, data: Any = None, exc_info: bool = False, event_message: Optional[str] = None):
        self._log("error", request_id, data, exc_info=exc_info, event_message=event_message)

    def start(self, request_id: str, data: Any = None, event_message: Optional[str] = None, level: str = "info"):
        self._start_times[request_id] = time.perf_counter()
        self._log(level, request_id, data, event_message=event_message or "start")

    def end(self, request_id: str, data: Any = None, event_message: Optional[str] = None, level: str = "info", **kwargs):
        start_time = self._start_times.pop(request_id, None)
        elapsed = (time.perf_counter() - start_time) * 1000.0 if start_time else None
        self._log(level, request_id, data, event_message=event_message or "end", elapsed_ms=elapsed)

    def shutdown(self):
        if hasattr(self, "_sock"):
            self._sock.close()
