from __future__ import annotations

import json
import uuid
import httpx
from typing import Any, Dict, List

from litestar import Router, get, post
from litestar.exceptions import HTTPException
from litestar.params import Body

from apps.const import resolve_path, STORAGE_BASE_URL, SF_SCHEMA_PATH
from apps.salesforce_app.server.sobjects.download_master import DownloadMaster

@get("/apex/schema")
async def get_schema() -> Dict[str, Any]:
    schema_path = SF_SCHEMA_PATH
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


@get("/apex/api/download-masters")
async def list_download_master() -> List[Dict[str, Any]]:
    return DownloadMaster.list()


@post("/apex/download-request")
async def download_request(data: Dict[str, Any] = Body()) -> List[Dict[str, Any]]:

    file_ids = data.get("file_ids")
    if not file_ids or not isinstance(file_ids, list):
        raise HTTPException(status_code=400, detail="file_ids is required")

    request_id = str(uuid.uuid4())
    storage_request_list: List[Dict[str, Any]] = []

    for fid in file_ids:
        dm = DownloadMaster.find(fid)

        if dm is None:
            print(f"[WARN] DownloadMaster not found: {fid}")
            continue

        updated = DownloadMaster.update(
            fid,
            {
                "Status__c": "Pending",
                "LastError__c": None,
            },
        )

        if not updated:
            print(f"[ERROR] Failed to update DownloadMaster: {fid}")
            continue

        storage_request_list.append(
            {
                "id": updated["id"],
                "filename": updated["filename"],
                "filename_disp": updated.get("filename_disp"),
                "encrypted_filepath": updated["encrypted_filepath"],
                "extension": updated["extension"],
                "status": updated.get("status", "Pending"),
            }
        )

    payload = {"request": storage_request_list}

    async with httpx.AsyncClient() as client:
        await client.post(
            f"{STORAGE_BASE_URL}/download-request",
            json=payload,
            headers={"X-Request-Id": request_id},
        )

    # ★ Litestar は dict/list を返せば自動で JSON にする
    return storage_request_list


apex_router = Router(
    path="/",
    route_handlers=[
        get_schema,
        list_download_master,
        download_request,
    ],
)
