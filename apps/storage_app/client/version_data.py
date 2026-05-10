# storage_server/app/version_data.py

from __future__ import annotations
import base64
from pathlib import Path

def iter_version_data_chunks(path: Path, chunk_size: int = 5 * 1024 * 1024):
    """
    Salesforce ContentVersion 用の VersionData chunk を生成する。
    - ファイルを chunk_size ごとに読み込む
    - Base64 エンコードして str を yield する
    """
    with path.open("rb") as f:
        while True:
            chunk = f.read(chunk_size)
            if not chunk:
                break
            yield base64.b64encode(chunk).decode("utf-8")
