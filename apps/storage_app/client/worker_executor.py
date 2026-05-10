# storage_server/app/worker/worker_executor.py

from __future__ import annotations
from pathlib import Path
import msgspec

from apps.storage_app.utils.crypto import decrypt_path, validate_path
from apps.storage_app.client.token import get_salesforce_token
from apps.storage_app.client.http_client import http_request_with_retry
from apps.storage_app.utils.queue_manager import (
    move_to_processing,
    move_to_completed,
)
from apps.storage_app.utils.logging_decorator import trace_action
from apps.storage_app.models.models import QueueModel, DownloadMaster__c
from apps.storage_app.utils.logging_context import bind_download_master, bind_request_id

from apps.const import (
    SF_URL_CONTENT_VERSION,
    sf_url_downloadmaster_record,
)

from apps.storage_app.client.version_data import iter_version_data_chunks

@trace_action
async def execute_download_job(queue_file: Path) -> None:
    """
    Queue に積まれた 1 ジョブ（1 ファイル）を処理する。

    - QueueModel を読み込み DownloadMaster__c を構築
    - encrypted_filepath を復号・検証
    - Salesforce に ContentVersion を POST（VersionData なし）
    - DownloadMaster__c を Completed に PATCH
    - 正常終了なら completed に移動
    - 例外は worker_loop に伝播（そこで move_to_error + notify_error）
    """

    processing_file = queue_file

    # 2. QueueModel 読み込み
    raw = processing_file.read_bytes()
    queue_item: QueueModel = msgspec.json.decode(raw, type=QueueModel)

    request_id = queue_item.request_id
    bind_request_id(request_id)

    dm = DownloadMaster__c(
        id=queue_item.id,
        filename=queue_item.filename,
        filename_disp=queue_item.filename_disp,
        encrypted_filepath=queue_item.encrypted_filepath,
        extension=queue_item.extension,
        status=queue_item.status,
    )
    bind_download_master(msgspec.to_builtins(dm))

    # 3. decrypt / validate / file existence check
    plaintext = decrypt_path(dm.encrypted_filepath)
    safe_path = validate_path(Path(plaintext))

    if not safe_path.exists():
        raise FileNotFoundError(f"File not found: {safe_path}")

    # 4. Salesforce Token
    token = await get_salesforce_token()

    version_data = "".join(iter_version_data_chunks(safe_path))

    # 5. ContentVersion POST（VersionData なし）
    initial_payload = {
        "Title": dm.filename,
        "PathOnClient": dm.filename,
        "FirstPublishLocationId": dm.id,
        "VersionData": version_data,
    }

    res = await http_request_with_retry(
        "POST",
        SF_URL_CONTENT_VERSION,
        json=initial_payload,
        headers={"Authorization": f"Bearer {token}"},
        request_id=request_id,
        download=dm,
    )
    res.raise_for_status()

    # 6. DownloadMaster__c を Completed に更新
    patch_payload = {
        "Status__c": "Completed",
        "LastError__c": "",
    }

    res2 = await http_request_with_retry(
        "PATCH",
        sf_url_downloadmaster_record(dm.id or ""),
        json=patch_payload,
        headers={"Authorization": f"Bearer {token}"},
        request_id=request_id,
        download=dm,
    )
    res2.raise_for_status()

    # 7. 完了
    move_to_completed(processing_file, delete=True)
