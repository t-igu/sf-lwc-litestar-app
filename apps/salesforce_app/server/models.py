# AUTO-GENERATED FILE. DO NOT EDIT MANUALLY.
# Generated from storage/schema/schema.json
import msgspec
import datetime

class DownloadMaster__c(msgspec.Struct):
    filename: str
    encrypted_filepath: str
    extension: str
    status: str = 'Pending'
    id: str | None = None
    filename_disp: str | None = None

class DownloadMasterWork__c(msgspec.Struct):
    filename: str
    encrypted_filepath: str
    extension: str
    status: str = 'Pending'
    id: str | None = None
    filename_disp: str | None = None

class QueueModel(msgspec.Struct):
    request_id: str
    id: str
    filename: str
    encrypted_filepath: str
    extension: str
    status: str = 'Pending'
    retry_count: int = 0
    filename_disp: str | None = None
    last_error: str | None = None

class SalesforceToken(msgspec.Struct):
    access_token: str
    instance_url: str
    token_type: str = 'Bearer'
    scope: str | None = None
