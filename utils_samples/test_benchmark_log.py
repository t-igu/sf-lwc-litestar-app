#!/usr/bin/env python3

import time
import os
import sys
from app.utils.log_utils.trace_log_socket import TraceLog # Import the socket version

def run_benchmark():
    log_file = "benchmark_100k.log"
    count = 100_000

    # テスト前に古いログを削除
    if os.path.exists(log_file):
        os.remove(log_file)

    # 10万件を確実に収容するため、queue_sizeを少し大きめに設定
    print(f"--- Benchmark Start: {count} logs ---")
    logger = TraceLog(service_name="bench-service") # Socket version doesn't take log_file or queue_size

    # 1. メインプロセスのスループット計測
    # (キューにデータを詰め込む速度 = アプリケーションが待たされる時間)
    start_time = time.perf_counter()

    for i in range(count):
        # 実際的な負荷として、辞書データを渡す
        logger.info(f"req-{i}", {
            "index": i,
            "payload": "python_performance_limit_test",
            "meta": {"test": True, "type": "benchmark"}
        })

    enqueue_duration = time.perf_counter() - start_time
    print(f"Enqueueing (Main Process) finished.")
    print(f"  Duration: {enqueue_duration:.4f} sec")
    print(f"  Throughput: {count / enqueue_duration:,.2f} logs/sec")

    print("\nFlushing to disk (Shutdown)...")

    # 2. ディスク書き込み完了までの時間を計測
    # shutdown() closes the socket. The daemon continues writing.
    logger.shutdown()

    total_duration = time.perf_counter() - start_time

    print(f"Write to Disk finished.")
    print(f"  Total Duration: {total_duration:.4f} sec")
    print(f"  Disk I/O Throughput: {count / total_duration:,.2f} logs/sec")

    # 実際のファイルサイズを確認
    if os.path.exists(log_file):
        size_mb = os.path.getsize(log_file) / (1024 * 1024)
        print(f"\nResulting file size: {size_mb:.2f} MB")

        # 行数確認 (100,000行 + 標準ログ出力がある場合はそれ以上)
        with open(log_file, 'rb') as f:
            line_count = sum(1 for _ in f)
        print(f"Total lines in file: {line_count:,}")
    else:
        print(f"Log file '{log_file}' not found. Ensure daemon is running and writing.", file=sys.stderr)

    print("\n--- Benchmark End ---")

if __name__ == "__main__":
    run_benchmark()
