# salesforce_server/app/sobjects/download_master.py

from __future__ import annotations

from .base import SObject
from apps.const import OBJECTS_DOWNLOAD_MASTER_DIR, OBJECTS_DOWNLOAD_MASTERWORK_DIR

class DownloadMaster(SObject):
    """
    Salesforce Mock の DownloadMaster__c SObject。
    JSON ファイルとして保存される。
    """
    OBJECTS_DIR = OBJECTS_DOWNLOAD_MASTER_DIR

class DownloadMasterWork(SObject):
    """
    Salesforce Mock の DownloadMaster__c SObject。
    JSON ファイルとして保存される。
    """
    OBJECTS_DIR = OBJECTS_DOWNLOAD_MASTERWORK_DIR
