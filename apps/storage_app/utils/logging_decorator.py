# storage_server/app/logging_decorator.py
from __future__ import annotations

import time
from functools import wraps
from apps.storage_app.utils.logging_utils import ordered_log, now_iso, get_request_id
import inspect
import functools
import msgspec
from httpx import Response as HttpxResponse
from litestar.response import Response as LITESTARResponse

from apps.storage_app.utils.logging_context import bind_request_id, bind_download_master
import structlog

# from apps.storage_app.logging_config import setup_logging
# setup_logging()
# server.py, worker_executor.py で setup_logging() を呼んでいるため、ここでは呼ばない

logger = structlog.get_logger()

# 対象となる msgspec.Struct 型
STRUCT_TYPES = (
    # 必要に応じて追加
    # DownloadMaster__c,
    # QueueModel,
    # SalesforceToken,
)

def serialize_value(val):
    """ログに出すための値を整形する"""
    # msgspec.Struct → dict
    if isinstance(val, STRUCT_TYPES):
        return msgspec.to_builtins(val)

    # httpx.Response
    if isinstance(val, HttpxResponse):
        try:
            body = val.json()
        except Exception:
            body = val.text
        return {
            "type": "httpx.Response",
            "status_code": val.status_code,
            "body": body,
        }

    # FastAPI Response
    if isinstance(val, LITESTARResponse):
        return {
            "type": "fastapi.Response",
            "status_code": val.status_code,
        }

    # その他はそのまま
    return val


def extract_request_id(args, kwargs):
    """request_id を引数から抽出"""
    if "request_id" in kwargs:
        return kwargs["request_id"]

    # args からも探す（名前付き引数でない場合）
    sig = inspect.signature(args[0].__class__) if args else None
    for name, val in kwargs.items():
        if name == "request_id":
            return val

    return None


logger = structlog.get_logger()

def trace_action(func):
    @wraps(func)
    async def wrapper(*args, **kwargs):
        log = structlog.get_logger()

        # ★ 位置引数 + キーワード引数を統合
        sig = inspect.signature(func)
        bound = sig.bind_partial(*args, **kwargs)
        all_params = bound.arguments

        # start log
        log.info(
            **ordered_log(
                request_id=get_request_id(),
                timestamp=now_iso(),
                function=func.__name__,
                method=all_params.get("method"),
                url=all_params.get("url"),
                parameters=all_params,   # ← これで全部入る
            ),
            event="start",
        )

        start = time.perf_counter()
        result = None
        try:
            result = await func(*args, **kwargs)
            return result
        finally:
            elapsed = int((time.perf_counter() - start) * 1000)

            # status_code 抽出（安全版）
            status_code: int | None = None

            if isinstance(result, dict):
                status_code = result.get("status_code")
            elif hasattr(result, "status_code"):
                # httpx.Response や FastAPI/Litestar Response を想定
                try:
                    status_code = getattr(result, "status_code", None)
                except Exception:
                    status_code = None
            # end log
            log.info(
                **ordered_log(
                    request_id=get_request_id(),
                    timestamp=now_iso(),
                    function=func.__name__,
                    method=all_params.get("method"),
                    url=all_params.get("url"),
                    parameters=None,
                    elapsed_ms=elapsed,
                    return_value=result,
                    status_code=status_code,
                ),
                event="end",
            )

    return wrapper
