from __future__ import annotations

import base64
import uuid
import asyncio
import httpx
from typing import Any, Dict

from litestar import post, patch, Request, Router
from litestar.exceptions import HTTPException

from apps.const import (
    OBJECTS_CONTENTVERSIONDATA_DIR,
    SF_BASE_URL,
)
from apps.salesforce_app.server.sobjects.download_master import DownloadMaster
from apps.salesforce_app.server.sobjects.content_version import ContentVersion
from apps.salesforce_app.server.sobjects.content_ducument_link import ContentDocumentLink

# ------------------------------------------------------------
# CDC Relay URL
# ------------------------------------------------------------
CDC_RELAY_URL = f"{SF_BASE_URL}/cdc/relay"

# ------------------------------------------------------------
# CDC Relay → LWC へイベント通知
# ------------------------------------------------------------
def push_cdc_event(id: str, status: str | None, doc_id: str | None):
    payload = {
        "id": id,
        "status": status,
        "content_document_id": doc_id,
        "event_type": "DownloadMaster__c",
    }

    async def send():
        async with httpx.AsyncClient() as client:
            await client.post(CDC_RELAY_URL, json=payload)
        print(f"[CDC] Relay sent: {payload}")

    asyncio.create_task(send())


# ------------------------------------------------------------
# ContentVersion (POST)
# ------------------------------------------------------------
@post("/ContentVersion")
async def create_content_version(request: Request) -> Dict[str, Any]:
    """
    VersionData(Base64) を受け取り、実体ファイルとして保存する Salesforce モック。
    FirstPublishLocationId を指定すると ContentDocumentLink を自動生成する。
    """
    data = await request.json()

    version_id = f"068{uuid.uuid4().hex[:12]}"
    document_id = f"069{uuid.uuid4().hex[:12]}"

    # -----------------------------
    # VersionData(Base64) → バイナリ保存
    # -----------------------------
    version_data_b64 = data.get("VersionData")
    if version_data_b64:
        try:
            file_bytes = base64.b64decode(version_data_b64)
        except Exception:
            raise HTTPException(status_code=400, detail="Invalid Base64 VersionData")

        # 保存先ディレクトリ（settings.py の定義を使用）
        OBJECTS_CONTENTVERSIONDATA_DIR.mkdir(parents=True, exist_ok=True)

        file_path = OBJECTS_CONTENTVERSIONDATA_DIR / version_id
        file_path.write_bytes(file_bytes)

    # -----------------------------
    # ContentVersion メタデータ保存
    # -----------------------------
    version_record = {
        "Id": version_id,
        "ContentDocumentId": document_id,
        "Title": data.get("Title"),
        "PathOnClient": data.get("PathOnClient"),
        "VersionData": version_data_b64,  # ← これが重要
        "FirstPublishLocationId": data.get("FirstPublishLocationId"),
    }

    ContentVersion.insert(version_id, version_record)

    # -----------------------------
    # FirstPublishLocationId → DownloadMaster__c に自動リンク
    # -----------------------------
    parent_id = data.get("FirstPublishLocationId")
    if parent_id:
        DownloadMaster.update(
            parent_id,
            {"ContentDocumentId__c": document_id},
        )

        ContentDocumentLink.insert(
            document_id,
            {
                "ContentDocumentId": document_id,
                "LinkedEntityId": parent_id,
                "ShareType": "V",
            },
        )

    return {"id": version_id, "ContentDocumentId": document_id}


# ------------------------------------------------------------
# DownloadMaster__c PATCH
# ------------------------------------------------------------
@patch("/DownloadMaster__c/{id:str}")
async def update_download_master(id: str, data: Dict[str, Any]) -> Dict[str, Any]:

    update_data: Dict[str, Any] = {}

    if "Status__c" in data:
        update_data["Status__c"] = data["Status__c"]

    status_map = {
        "Completed": "Completed",
        "完了": "Completed",
        "Error": "Error",
        "失敗": "Error",
    }
    if data.get("Status__c") in status_map:
        update_data["status"] = status_map[data["Status__c"]]

    if "ContentDocumentId__c" in data:
        update_data["ContentDocumentId__c"] = data["ContentDocumentId__c"]

    record = DownloadMaster.update(id, update_data)
    if record is None:
        raise HTTPException(status_code=404, detail="not found")

    push_cdc_event(
        id=id,
        status=record.get("status"),
        doc_id=record.get("ContentDocumentId__c"),
    )

    return {"success": True}

restapi_router = Router(
    path="/services/data/v60.0/sobjects",
    route_handlers=[create_content_version, update_download_master],
)
