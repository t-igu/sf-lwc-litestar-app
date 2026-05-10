# salesforce_server/app/sobjects/base.py

from __future__ import annotations
import json
from pathlib import Path
from typing import Optional


class SObject:
    """
    Salesforce Mock の SObject 基底クラス。
    各 SObject クラスは OBJECTS_DIR を設定して使用する。
    """
    OBJECTS_DIR: Optional[Path] = None

    @classmethod
    def _ensure_dir(cls) -> Path:
        if cls.OBJECTS_DIR is None:
            raise RuntimeError(f"{cls.__name__}.OBJECTS_DIR が設定されていません")
        cls.OBJECTS_DIR.mkdir(parents=True, exist_ok=True)
        return cls.OBJECTS_DIR

    @classmethod
    def _file(cls, record_id: str) -> Path:
        base = cls._ensure_dir()
        return base / f"{record_id}.json"

    @classmethod
    def find(cls, record_id: str):
        file = cls._file(record_id)
        if not file.exists():
            return None
        with open(file, "r", encoding="utf-8") as f:
            return json.load(f)

    @classmethod
    def insert(cls, record_id: str, data: dict):
        file = cls._file(record_id)
        with open(file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return data

    @classmethod
    def update(cls, record_id: str, updates: dict):
        record = cls.find(record_id)
        if record is None:
            return None
        record.update(updates)
        cls.insert(record_id, record)
        return record

    @classmethod
    def delete(cls, record_id: str):
        file = cls._file(record_id)
        if file.exists():
            file.unlink()
            return True
        return False

    @classmethod
    def list(cls):
        base = cls._ensure_dir()
        results = []
        for file in base.glob("*.json"):
            with open(file, "r", encoding="utf-8") as f:
                results.append(json.load(f))
        return results
