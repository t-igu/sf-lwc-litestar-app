import asyncio

import httpx
from httpx import Response

from apps.storage_app.utils.logging_decorator import trace_action
from apps.const import HTTP_RETRY_COUNT, HTTP_RETRY_DELAY

@trace_action
async def http_request_with_retry(method: str, url: str, **kwargs) -> Response:
    """
    httpx を使ったシンプルなリトライ付き HTTP リクエスト。
    - request_id / download は trace_action が拾うため httpx に渡さない。
    - HTTP_RETRY_COUNT / HTTP_RETRY_DELAY は const.py で管理。
    """

    # trace_action 用メタ情報を除去
    kwargs.pop("request_id", None)
    kwargs.pop("download", None)

    async with httpx.AsyncClient(timeout=30) as client:
        for attempt in range(HTTP_RETRY_COUNT):
            try:
                return await client.request(method, url, **kwargs)

            except httpx.RequestError:
                if attempt == HTTP_RETRY_COUNT - 1:
                    raise
                await asyncio.sleep(HTTP_RETRY_DELAY)

    # Pylance 対策（ここには到達しない）
    raise RuntimeError("unreachable")
