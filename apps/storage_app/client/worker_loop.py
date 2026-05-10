# storage_server/app/worker/worker_loop.py

from __future__ import annotations

import asyncio
from pathlib import Path

from apps.storage_app.utils.queue_manager import QUEUE_ACCEPTED_DIR, move_to_error, move_to_processing
from apps.storage_app.client.worker_executor import execute_download_job
from apps.storage_app.client.notify import notify_error
from apps.storage_app.utils.logging_config import setup_logging

setup_logging()

async def worker_loop(poll_interval: float = 0.05):
    print(f"[worker] started (poll_interval={poll_interval}s)")

    while True:
        # 1. accepted キューから 1 件だけ取る
        queue_file: Path | None = next(QUEUE_ACCEPTED_DIR.glob("*.json"), None)

        if not queue_file:
            await asyncio.sleep(poll_interval)
            continue

        try:

            queue_file = move_to_processing(queue_file)

            # 2. ジョブ実行（例外はそのまま raise）
            await execute_download_job(queue_file)

        except Exception as e:

            # 4. queue を error に移動
            move_to_error(queue_file)

            # 3. Salesforce にエラー通知
            await notify_error(queue_file.stem, str(e))


            # 5. Worker は継続
            continue

# ------------------------------------------------------------
# main entrypoint
# ------------------------------------------------------------
if __name__ == "__main__":
    asyncio.run(worker_loop())
