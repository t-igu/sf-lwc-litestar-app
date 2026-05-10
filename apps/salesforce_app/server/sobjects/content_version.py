# salesforce_server/app/sobjects/content_version.py

from __future__ import annotations

from .base import SObject
from apps.const import OBJECTS_CONTENTVERSION_DIR

class ContentVersion(SObject):
    """
    Salesforce Mock の ContentVersion SObject。
    JSON ファイルとして保存される。
    """
    OBJECTS_DIR = OBJECTS_CONTENTVERSION_DIR
    @classmethod
    def find_by_document_id(cls, doc_id: str):
        """
        ContentDocumentId → ContentVersion を検索する
        """
        for rec in cls.list():
            if rec.get("ContentDocumentId") == doc_id:
                return rec
        return None

