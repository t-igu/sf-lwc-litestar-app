from __future__ import annotations
from pathlib import Path

from .base import SObject
from apps.const import OBJECTS_CONTENTVERSIONDATA_DIR

class ContentVersionData(SObject):
    """
    Salesforce Mock の ContentVersionData SObject。
    - JSON: メタデータ（FilePath など）
    - 実体ファイル: バイナリ
    """
    OBJECTS_DIR = OBJECTS_CONTENTVERSIONDATA_DIR

    @classmethod
    def binary_path(cls, version_id: str) -> Path:
        """
        version_id に対応する実体ファイルのパスを返す。
        """
        if not cls.OBJECTS_DIR:
            raise RuntimeError(f"{cls.__name__}.OBJECTS_DIR が設定されていません")
        return Path(cls.OBJECTS_DIR) / version_id

    @classmethod
    def exists(cls, version_id: str) -> bool:
        """
        version_id の実体ファイルが存在するか？
        """
        return cls.binary_path(version_id).exists()

    @classmethod
    def iter_binary(cls, version_id: str, chunk_size: int = 1024 * 1024):
        """
        実体ファイルを chunk で読み込むジェネレータ。
        StreamingResponse に渡す用途。
        """
        file_path = cls.binary_path(version_id)
        
        if not file_path.exists():
            raise FileNotFoundError(f"VersionData not found: {file_path}")

        with open(file_path, "rb") as f:
            while True:
                chunk = f.read(chunk_size)
                if not chunk:
                    break
                yield chunk
