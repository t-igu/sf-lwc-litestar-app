# salesforce_server/app/sobjects/content_version.py

from __future__ import annotations

from .base import SObject
from apps.const import OBJECTS_CONTENTDOCUMENTLINK_DIR

class ContentDocumentLink(SObject):
    """
    Salesforce Mock の ContentVersion SObject。
    JSON ファイルとして保存される。
    """
    OBJECTS_DIR = OBJECTS_CONTENTDOCUMENTLINK_DIR
