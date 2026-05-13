# storage_server/app/logging_config.py

import logging
import structlog
from apps.const import LOG_OUTPUT_DIR, LOG_OUTPUT_PATH, LOG_LEVEL

LOG_OUTPUT_DIR.parent.mkdir(parents=True, exist_ok=True)

def setup_logging():
    # ---------------------------------------------------------
    # 1. handlers を作成
    # ---------------------------------------------------------
    file_handler = logging.FileHandler(LOG_OUTPUT_PATH, encoding="utf-8")
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter("%(message)s"))

    # ---------------------------------------------------------
    # 2. root logger は file のみ
    # ---------------------------------------------------------
    root_logger = logging.getLogger()
    root_logger.setLevel(LOG_LEVEL)
    root_logger.handlers = [file_handler]   # ★ file のみ
    root_logger.propagate = False

    # ---------------------------------------------------------
    # 3. console は標準ログだけ
    # ---------------------------------------------------------
    console_logger = logging.getLogger("console")
    console_logger.setLevel(LOG_LEVEL)
    console_logger.addHandler(console_handler)
    console_logger.propagate = False

    # ---------------------------------------------------------
    # 4. FastAPI / httpx の logger を file に出す
    # ---------------------------------------------------------
    for name in ["fastapi", "httpx", "uvicorn.access", "uvicorn.error"]:
        lg = logging.getLogger(name)
        lg.setLevel(logging.INFO)
        lg.addHandler(file_handler)
        lg.propagate = False

    # ---------------------------------------------------------
    # 5. structlog → root logger（file のみ）
    # ---------------------------------------------------------
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            structlog.stdlib.ProcessorFormatter.wrap_for_formatter,
        ],
        logger_factory=structlog.stdlib.LoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
        cache_logger_on_first_use=True,
    )

    # file に JSON を書く
    json_formatter = structlog.stdlib.ProcessorFormatter(
        processor=structlog.processors.JSONRenderer(),
        foreign_pre_chain=[
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso"),
        ],
    )

    file_handler.setFormatter(json_formatter)
