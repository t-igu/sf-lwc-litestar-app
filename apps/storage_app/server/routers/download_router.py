from __future__ import annotations

import asyncio
from pathlib import Path
import msgspec

from litestar import Router, post, Request
from litestar.params import Body, Parameter
from litestar.exceptions import HTTPException

from apps.storage_app.models.models import QueueModel, DownloadMaster__c
from apps.storage_app.utils.queue_manager import create_queue_file
from apps.storage_app.client.notify import notify_error
from apps.storage_app.utils.logging_decorator import trace_action
from apps.storage_app.utils.crypto import decrypt_path, validate_path


# ------------------------------------------------------------
# msgspec decoder
# ------------------------------------------------------------
class DownloadRequest(msgspec.Struct):
    request: list[DownloadMaster__c]


decoder = msgspec.json.Decoder(type=DownloadRequest)


# ------------------------------------------------------------
# Queue 出力処理
# ------------------------------------------------------------
@trace_action
async def output_queue(request_id: str, masters: list[DownloadMaster__c]):
    """
    Apex Mock → Storage に送られた DownloadMaster__c の list を処理し、
    QueueModel に変換して queue/accepted に保存する。
    Worker は queue/accepted を監視して処理する。
    """

    for dm in masters:
        dm_id = dm.id or dm.filename
        try:
            decrypted = decrypt_path(dm.encrypted_filepath)
            safe_path = validate_path(Path(decrypted))
        except Exception as e:
            await notify_error(dm_id, str(e))
            # continue

        queue_item = QueueModel(
            request_id=request_id,
            id=dm_id,
            filename=dm.filename,
            encrypted_filepath=dm.encrypted_filepath,
            extension=dm.extension,
            status="Pending",
            retry_count=0,
            last_error=None,
        )

        create_queue_file(queue_item)

    print(f"[output_queue] Completed processing request_id={request_id}")

# ------------------------------------------------------------
# Download Request Handler
# ------------------------------------------------------------
@trace_action
async def handle_download_request(request: Request, request_id: str):
    raw = await request.body()
    data = decoder.decode(raw)
    downloads = data.request

    # ★ Litestar には BackgroundTasks がない → asyncio.create_task を使う
    asyncio.create_task(output_queue(request_id, downloads))

    return {
        "status": "accepted",
        "request_id": request_id,
    }

# ------------------------------------------------------------
# POST /download-request
# ------------------------------------------------------------
@post("/download-request", status_code=202)
async def create_download_request(
    request: Request,
    request_id: str = Parameter(None, header="X-Request-Id"),
)->dict:
    if not request_id:
        raise HTTPException(status_code=400, detail="Missing X-Request-Id")

    return await handle_download_request(request, request_id)

router = Router(
    path="/",
    route_handlers=[
        create_download_request,
    ],
)
