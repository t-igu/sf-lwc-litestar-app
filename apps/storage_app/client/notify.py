# storage_server/app/worker/notify.py

from __future__ import annotations

from apps.const import (
    sf_url_downloadmaster_record,
)
from apps.storage_app.client.http_client import http_request_with_retry
from apps.storage_app.client.token import get_salesforce_token
from apps.storage_app.utils.logging_decorator import trace_action


@trace_action
async def notify_error(dm_id: str, message: str) -> None:
    """
    DownloadMaster__c にエラー状態を通知する。
    - 例外はそのまま raise（trace_action がログを出す）
    - Worker 全体は worker_loop 側で継続される
    """

    token = await get_salesforce_token()

    payload = {
        "Status__c": "Error",
        "LastError__c": message,
    }

    res = await http_request_with_retry(
        "PATCH",
        sf_url_downloadmaster_record(dm_id),
        json=payload,
        headers={"Authorization": f"Bearer {token}"},
    )
    res.raise_for_status()
