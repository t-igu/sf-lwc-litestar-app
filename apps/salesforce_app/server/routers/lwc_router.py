from __future__ import annotations

import mimetypes
from litestar.static_files import create_static_files_router

from litestar import Router, get
from litestar.response import File
from litestar.exceptions import HTTPException
from apps.const import OBJECTS_ROOT, LWC_DIST_DIR, LWC_STATIC_DIR, OBJECTS_CONTENTVERSIONDATA_DIR
from apps.salesforce_app.server.sobjects.content_version import ContentVersion
from apps.salesforce_app.server.sobjects.content_version_data import ContentVersionData

# ------------------------------------------------------------
# LWC OSS の静的ファイルディレクトリ
# ------------------------------------------------------------

if not LWC_DIST_DIR.exists():
    print("\n" + "=" * 60)
    print(f"警告: LWC dist ディレクトリが見つかりません: {LWC_DIST_DIR}")
    print("先に 'cd salesforce_lwc && npm run build' を実行してください。")
    print("=" * 60 + "\n")

if not OBJECTS_ROOT.exists():
    print("\n" + "=" * 60)
    print(f"警告: objects_root ディレクトリが見つかりません: {OBJECTS_ROOT}")
    print("=" * 60 + "\n")

print(f"[LWC] STATIC_DIST_DIR = {LWC_DIST_DIR}")
print(f"[LWC] LWC_PUBLIC_DIR = {LWC_STATIC_DIR}")
print(f"[LWC] OBJECTS_DIR = {OBJECTS_ROOT}")

# ------------------------------------------------------------
# Salesforce のファイルダウンロード URL 模倣
# ------------------------------------------------------------
@get("/sfc/servlet.shepherd/version/download/{doc_id:str}")
async def mock_download(doc_id: str)->File:

    version = ContentVersion.find_by_document_id(doc_id)

    if not version:
        raise HTTPException(status_code=404, detail="ContentVersion not found")

    version_id = version["Id"]

    if not ContentVersionData.exists(version_id):
        raise HTTPException(status_code=404, detail="VersionData not found")

    # 2. バイナリ存在チェック
    if not ContentVersionData.exists(version_id):
        raise HTTPException(status_code=404, detail="VersionData not found")

    filename = version.get("Title") or "download.bin"
    mime, _ = mimetypes.guess_type(filename)
    content_type = mime or "application/octet-stream"

    file_path = OBJECTS_CONTENTVERSIONDATA_DIR / version_id

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="Binary not found")

    # 3. Litestar の File を返す（これが正解）
    return File(
        path=file_path,
        filename=filename,
        media_type=content_type
    )    
# ------------------------------------------------------------
# LWC OSS の静的ファイル配信
# ------------------------------------------------------------
lwc_static_router = create_static_files_router(
    path="/",
    directories=[LWC_DIST_DIR, LWC_STATIC_DIR],
    html_mode=True,
)

lwc_router = Router(
    path="/",
    route_handlers=[lwc_static_router, mock_download],
)
