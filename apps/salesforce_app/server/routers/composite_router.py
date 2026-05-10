# apps/salesforce_app/server/routers/composite_router.py

from __future__ import annotations
import uuid
from typing import Any

import msgspec
from litestar import Router, post, Request
from litestar.exceptions import HTTPException

from apps import const

# sobjects（永続化）
from apps.salesforce_app.server.sobjects.download_master import DownloadMaster
from apps.salesforce_app.server.sobjects.download_master import DownloadMasterWork


# -----------------------------
# Composite API 型定義
# -----------------------------
class CompositeSubRequest(msgspec.Struct):
    method: str
    url: str
    referenceId: str
    body: dict[str, Any] | None = None

class CompositeRequest(msgspec.Struct):
    allOrNone: bool = False
    compositeRequest: list[CompositeSubRequest] = msgspec.field(default_factory=list)
    
class CompositeSubResponse(msgspec.Struct):
    httpStatusCode: int
    referenceId: str
    body: dict[str, Any] | None = None


class CompositeResponse(msgspec.Struct):
    compositeResponse: list[CompositeSubResponse]


decoder = msgspec.json.Decoder(type=CompositeRequest)
encoder = msgspec.json.Encoder()


# -----------------------------
# Composite Entry
# -----------------------------
@post("/composite")
async def composite_entry(request: Request) -> bytes:
    raw = await request.body()
    try:
        comp_req = decoder.decode(raw)
    except msgspec.DecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid composite payload: {e}")

    subreqs = comp_req.compositeRequest
    if len(subreqs) > 25:
        raise HTTPException(status_code=400, detail="Too many subrequests (max 25)")

    responses: list[CompositeSubResponse] = []

    for sub in subreqs:
        method = sub.method.upper()
        url = sub.url
        ref_id = sub.referenceId

        # DownloadMasterWork__c Insert のみ対応
        if method == "POST" and "sobjects/DownloadMasterWork__c" in url:
            res = _handle_work_insert(sub.body or {}, ref_id)
            responses.append(res)
        else:
            responses.append(
                CompositeSubResponse(
                    httpStatusCode=400,
                    referenceId=ref_id,
                    body={"error": "Unsupported subrequest", "url": url, "method": method},
                )
            )

    return encoder.encode(CompositeResponse(compositeResponse=responses))


# -----------------------------
# Work Insert → Master Upsert → Work Delete
# -----------------------------
def _handle_work_insert(body: dict[str, Any], ref_id: str) -> CompositeSubResponse:
    """
    1. DownloadMasterWork__c Insert
    2. Apex の代わりに DownloadMaster__c Upsert
    3. DownloadMasterWork__c Delete
    """

    # -----------------------------
    # 1. Work Insert
    # -----------------------------
    work_id = f"DMW-{uuid.uuid4().hex[:12]}"
    work_record = {
        "id": work_id,
        "filename": body["Filename__c"],
        "filename_disp": body.get("FilenameDisp__c"),
        "encrypted_filepath": body["EncryptedFilepath__c"],
        "extension": body["Extension__c"],
        "status": body.get("Status__c", "Pending"),
    }

    DownloadMasterWork.insert(work_id, work_record)

    # -----------------------------
    # 2. Master Upsert（filename を External ID として扱う）
    # -----------------------------
    filename = work_record["filename"]

    existing = None
    for rec in DownloadMaster.list():
        if rec.get("filename") == filename:
            existing = rec
            break

    if existing:
        # Update
        DownloadMaster.update(existing["id"], {
            "filename_disp": work_record["filename_disp"],
            "encrypted_filepath": work_record["encrypted_filepath"],
            "extension": work_record["extension"],
            "status": work_record["status"],
        })
        master_id = existing["id"]
    else:
        # Insert
        master_id = f"DM-{uuid.uuid4().hex[:12]}"
        DownloadMaster.insert(master_id, {
            "id": master_id,
            "filename": filename,
            "filename_disp": work_record["filename_disp"],
            "encrypted_filepath": work_record["encrypted_filepath"],
            "extension": work_record["extension"],
            "status": work_record["status"],
        })

    # -----------------------------
    # 3. Work Delete（Apex の動きの再現）
    # -----------------------------
    DownloadMasterWork.delete(work_id)

    # -----------------------------
    # Composite Response
    # -----------------------------
    return CompositeSubResponse(
        httpStatusCode=200,
        referenceId=ref_id,
        body={"id": master_id, "success": True},
    )

# Router（restapi と同じベースパス）
router = Router(
    path="/services/data/v60.0",
    route_handlers=[composite_entry],
)
