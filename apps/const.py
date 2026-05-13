# settings.py (fixed constants, no config loader)

from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent

# ============================================================
# Logging
# ============================================================

LOG_OUTPUT_DIR = BASE_DIR / "data" / "storage" / "logs"
LOG_OUTPUT_PATH = LOG_OUTPUT_DIR / "app.log"
LOG_LEVEL = "INFO"

# data\storage\logs
# decript, encript key
# import os, base64
# print(base64.b64encode(os.urandom(32)).decode())
AES_KEY = "q0ioJtYQE7Av5lLlCPq4CmsZQEGLDSjGvqcDCl2GWAs="

# ============================================================
# Salesforce REST API
# ============================================================
SF_HOST = "127.0.0.1"
SF_PORT = "8000"

SF_BASE_URL = f"http://{SF_HOST}:{SF_PORT}/services/data/v60.0"

SF_URL_CONTENT_VERSION = f"{SF_BASE_URL}/sobjects/ContentVersion"
SF_URL_DOWNLOADMASTER = f"{SF_BASE_URL}/sobjects/DownloadMaster__c"

def sf_url_contentversion_record(record_id: str) -> str:
    return f"{SF_URL_CONTENT_VERSION}/{record_id}"

def sf_url_downloadmaster_record(record_id: str) -> str:
    return f"{SF_URL_DOWNLOADMASTER}/{record_id}"

SF_URL_TOKEN = "http://127.0.0.1:8000/services/oauth2/token"


LWC_DIST_DIR = BASE_DIR / "apps/salesforce_app/lwc/dist"
LWC_STATIC_DIR = BASE_DIR / "apps/salesforce_app/lwc/src/public"

SF_SCHEMA_PATH = BASE_DIR / "data/storage/schema/schema.json"

# ============================================================
# Salesforce Auth (JWT Bearer Flow)
# ============================================================
SF_GRANT_TYPE_JWT = "urn:ietf:params:oauth:grant-type:jwt-bearer"
SF_CLIENT_ID = "mock-client-id"
SF_USERNAME = "mock-user@example.com"
SF_AUDIENCE = "http://127.0.0.1:8000"

TOKEN_CACHE_FILE = BASE_DIR / "data" / "storage" / "secret_key" / "sf_token.json"

SF_PRIVATE_KEY_PATH = BASE_DIR / "data" / "storage" / "secret_key" / "sf_private_key.pem"
with open(SF_PRIVATE_KEY_PATH, "r") as f:
    SF_PRIVATE_KEY = f.read()

SF_PUBLIC_KEY_PATH = BASE_DIR / "data" / "storage" / "secret_key" / "sf_public_key.pem"
with open(SF_PUBLIC_KEY_PATH, "r") as f:
    SF_PUBLIC_KEY = f.read()



# ============================================================
# SalesForce Objects directory
# ============================================================
OBJECTS_ROOT = BASE_DIR / "data/salesforce/objects"
OBJECTS_DOWNLOAD_MASTER_DIR = OBJECTS_ROOT / "DownloadMaster__c" 
OBJECTS_DOWNLOAD_MASTERWORK_DIR = OBJECTS_ROOT / "DownloadMasterWork__c" 
OBJECTS_CONTENTVERSION_DIR = OBJECTS_ROOT / "ContentVersion" 
OBJECTS_CONTENTVERSIONDATA_DIR = OBJECTS_ROOT / "ContentVersionData" 
OBJECTS_CONTENTDOCUMENTLINK_DIR = OBJECTS_ROOT / "ContentDocumentLink" 

# ============================================================
# Storage API 
# ============================================================
STORAGE_HOST = "127.0.0.1"
STORAGE_PORT = "8080"
STORAGE_BASE_URL = f"http://{STORAGE_HOST}:{STORAGE_PORT}"

# ============================================================
# Storage Queue directory
# ============================================================
QUEUE_ROOT = BASE_DIR / "data/storage/queue"
QUEUE_CREATE_DIR = QUEUE_ROOT/ "temp"
QUEUE_ACCEPTED_DIR = QUEUE_ROOT/ "accepted"
QUEUE_PROCESSING_DIR = QUEUE_ROOT/ "processing"
QUEUE_COMPLETED_DIR = QUEUE_ROOT/ "completed"
QUEUE_ERROR_DIR = QUEUE_ROOT/ "error"


# ============================================================
# Storage FILE directory
# ============================================================
STORAGE_FILE_ROOT = BASE_DIR / "data/storage/data"


# ============================================================
# HTTP Retry Policy
# ============================================================
HTTP_RETRY_COUNT = 3
HTTP_RETRY_DELAY = 1.0  # seconds

def resolve_path(relative: str | Path) -> Path:
    return BASE_DIR / Path(relative)

# Debug print (optional)
if __name__ == "__main__":
    print(f"SF_BASE_URL: {SF_BASE_URL}")
    print(f"SF_URL_CONTENT_VERSION: {SF_URL_CONTENT_VERSION}")
    print(f"SF_URL_DOWNLOADMASTER: {SF_URL_DOWNLOADMASTER}")
    print(f"SF_URL_TOKEN: {SF_URL_TOKEN}")
    print(f"LOG_OUTPUT_PATH: {LOG_OUTPUT_PATH} LEVEL: {LOG_LEVEL}")
    print(f"QUEUE_ACCEPTED_DIR: {QUEUE_ACCEPTED_DIR}")
    print(f"QUEUE_PROCESSING_DIR: {QUEUE_PROCESSING_DIR}")
    print(f"QUEUE_COMPLTED_DIR: {QUEUE_COMPLETED_DIR}")
    print(f"HTTP_RETRY_COUNT: {HTTP_RETRY_COUNT} DELAY: {HTTP_RETRY_DELAY}")
