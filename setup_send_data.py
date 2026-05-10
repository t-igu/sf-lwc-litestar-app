import asyncio
from apps.storage_app.client.download_master_sync import send_download_masters_composite
import glob
from pathlib import Path

from apps.const import STORAGE_FILE_ROOT, SF_BASE_URL
import time


# ルート配下の全ファイルを対象
storage_dir = STORAGE_FILE_ROOT
files = glob.glob(f"{storage_dir}/**/*.*", recursive=True)

print(files)

asyncio.run(send_download_masters_composite(files))