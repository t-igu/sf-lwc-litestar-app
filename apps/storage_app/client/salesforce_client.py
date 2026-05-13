# apps/storage_app/client/salesforce_client.py

from __future__ import annotations
import asyncio
import httpx
import msgspec
from httpx import Response

from apps.const import (
    HTTP_RETRY_COUNT,
    HTTP_RETRY_DELAY,
    SF_BASE_URL,
)
from apps.storage_app.client.token import get_salesforce_token, clear_token_cache
from apps.storage_app.utils.logging_decorator import trace_action


class SalesforceClient:
    """
    Salesforce REST API クライアント
    - token 自動付与
    - 401 のとき自動 refresh
    - retry 内蔵
    """

    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    # ------------------------------------------------------------
    # 内部: retry + token 自動付与
    # ------------------------------------------------------------
    @trace_action
    async def _request(self, method: str, url: str, **kwargs) -> Response:
        token = await get_salesforce_token()

        # Authorization を自動付与
        headers = kwargs.pop("headers", {})
        headers["Authorization"] = f"Bearer {token}"
        kwargs["headers"] = headers

        async with httpx.AsyncClient(timeout=self.timeout) as client:
            for attempt in range(HTTP_RETRY_COUNT):
                try:
                    res = await client.request(method, url, **kwargs)

                    # 401 → token refresh → retry
                    if res.status_code == 401:
                        clear_token_cache()
                        token = await get_salesforce_token()
                        headers["Authorization"] = f"Bearer {token}"
                        continue

                    return res

                except httpx.RequestError:
                    if attempt == HTTP_RETRY_COUNT - 1:
                        raise
                    await asyncio.sleep(HTTP_RETRY_DELAY)

        raise RuntimeError("unreachable")

    # ------------------------------------------------------------
    # 公開 API
    # ------------------------------------------------------------
    async def get(self, path: str, **kwargs) -> Response:
        return await self._request("GET", SF_BASE_URL + path, **kwargs)

    async def post(self, path: str, **kwargs) -> Response:
        return await self._request("POST", SF_BASE_URL + path, **kwargs)

    async def patch(self, path: str, **kwargs) -> Response:
        return await self._request("PATCH", SF_BASE_URL + path, **kwargs)

    async def delete(self, path: str, **kwargs) -> Response:
        return await self._request("DELETE", SF_BASE_URL + path, **kwargs)

    # ------------------------------------------------------------
    # よく使う Salesforce API の helper
    # ------------------------------------------------------------
    async def create_sobject(self, object_name: str, data: dict) -> Response:
        return await self.post(f"/services/data/v61.0/sobjects/{object_name}", json=data)

    async def update_sobject(self, object_name: str, record_id: str, data: dict) -> Response:
        return await self.patch(f"/services/data/v61.0/sobjects/{object_name}/{record_id}", json=data)

    async def composite(self, body: dict) -> Response:
        return await self.post("/services/data/v61.0/composite", json=body)
