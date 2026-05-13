import contextvars
from typing import Optional, Dict, Any
import structlog

request_id_var: contextvars.ContextVar[Optional[str]] = contextvars.ContextVar(
    "request_id", default=None
)

download_master_var: contextvars.ContextVar[Optional[Dict[str, Any]]] = (
    contextvars.ContextVar("download_master", default=None)
)

def bind_request_id(request_id: Optional[str]):
    request_id_var.set(request_id)
    structlog.contextvars.bind_contextvars(request_id=request_id)

def bind_download_master(dm: Optional[Dict[str, Any]]):
    download_master_var.set(dm)
    structlog.contextvars.bind_contextvars(download_master=dm)

def clear_context():
    request_id_var.set(None)
    download_master_var.set(None)
    structlog.contextvars.bind_contextvars(
        request_id=None,
        download_master=None,
    )
