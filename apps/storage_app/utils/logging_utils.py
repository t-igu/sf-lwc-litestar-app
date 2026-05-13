# storage_server/app/logging_utils.py
from collections import OrderedDict
import time
import structlog

def now_iso():
    return time.strftime("%Y-%m-%dT%H:%M:%S")

def get_request_id():
    ctx = structlog.contextvars.get_contextvars()
    return ctx.get("request_id")

def ordered_log(
    request_id=None,
    timestamp=None,
    function=None,
    method=None,
    url=None,
    parameters=None,
    status_code=None,
    elapsed_ms=None,
    return_value=None,
):
    return OrderedDict([
        ("request_id", request_id),
        ("timestamp", timestamp),
        ("function", function),
        ("method", method),
        ("url", url),
        ("parameters", parameters),
        ("status_code", status_code),
        ("elapsed_ms", elapsed_ms),
        ("return_value", return_value),
    ])
