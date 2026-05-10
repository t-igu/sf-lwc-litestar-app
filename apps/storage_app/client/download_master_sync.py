from __future__ import annotations

import glob
from pathlib import Path

from apps.const import STORAGE_FILE_ROOT, SF_BASE_URL
from apps.storage_app.client.http_client import http_request_with_retry
from apps.storage_app.client.token import get_salesforce_token
from apps.storage_app.models.models import DownloadMasterWork__c
from apps.storage_app.utils.crypto import encrypt_path

def get_composite_chunk_list(items, chunk=25):
    for i in range(0, len(items), chunk):
        yield items[i:i+chunk]


async def send_download_masters_composite(files):
    """
    DownloadMasterWork__c を 25件ずつ Composite API に Insert 送信する
    """
    token = await get_salesforce_token()
    url = f"{SF_BASE_URL}/composite"


    for batch in get_composite_chunk_list(files):
        composite_body = {
            "allOrNone": False,
            "compositeRequest": []
        }

        for idx, file_path in enumerate(batch):
            ref_id = f"ref{idx}"
            p = Path(file_path)

            encrypted_path = encrypt_path(p)

            dmw = DownloadMasterWork__c(
                filename=p.name,
                filename_disp=p.stem,
                encrypted_filepath=encrypted_path,
                extension=p.suffix.lstrip("."),
                status="Pending",
            )

            composite_body["compositeRequest"].append({
                "method": "POST",
                "url": f"{SF_BASE_URL}/sobjects/DownloadMasterWork__c",
                "referenceId": ref_id,
                "body": {
                    "Filename__c": dmw.filename,
                    "FilenameDisp__c": dmw.filename_disp,
                    "EncryptedFilepath__c": dmw.encrypted_filepath,
                    "Extension__c": dmw.extension,
                    "Status__c": dmw.status,
                }
            })

        # Composite API 呼び出し
        res = await http_request_with_retry(
            "POST",
            url,
            json=composite_body,
            headers={"Authorization": f"Bearer {token}"},
        )

        res.raise_for_status()
        print(f"[Composite] sent {len(batch)} DownloadMasterWork__c items")
