#!/usr/bin/env python3

import time
import logging
import msgspec # Keep msgspec for TestData
from app.utils.log_utils.trace_log import TraceLog # Import the socket version

# msgspec.Struct を使ったテストデータ定義
class TestData(msgspec.Struct):
    user_id: int
    action: str
    metadata: dict[str, str]

def main():
    log_file = "./test_trace.log"
    print("Initializing logger...")
    # 1. ロガーの初期化
    logger = TraceLog(log_file=log_file)
    print("Logger initialized.")

    with logger:
        # 2. 各ログレベルのメソッドテスト
        print("Testing basic logging methods...")
        logger.start("req-101")
        logger.info({"message": "Informational log"}, event_message="Custom Info Event")
        logger.trace({"detail": "Low-level trace data"}, event_message="Custom Trace Event")
        logger.debug(TestData(user_id=1, action="login", metadata={"browser": "chrome"}), event_message="User Login")
        logger.warning({"issue": "Slow response detected"}, event_message="Performance Warning")
        logger.error({"critical_data": "corrupted"}, event_message="Data Corruption Error")
        # 3. start / end メソッドによる計測テスト
        print("Testing start/end measurement...")
        request_id = "req-201"
        logger.start(request_id, {"task": "database_query"}, event_message="DB Query Start")
        time.sleep(0.15)  # 擬似的な処理待ち
        logger.end({"rows_found": 42}, event_message="DB Query End")

        # 3.1 start / end メソッドのデフォルトイベントメッセージのテスト
        request_id_default = "req-202"
        logger.start(request_id_default, {"operation": "file_read"}, level="debug") # event should be "start"
        time.sleep(0.05)
        logger.end( {"bytes_read": 1024}) # event should be "end"

        # 4. 例外（error）のテスト
        print("Testing error logging with stacktrace...")
        try:
            1 / 0
        except ZeroDivisionError as e:
            logger.error({"error": "division by zero"}, exc_info=e, event_message="Zero Division Attempt")

        # 5. 標準 logging モジュールの統合テスト (FastAPI/httpx 等のログを取り込む想定)
        print("Testing standard logging integration...")
        std_logger = logging.getLogger("httpx")
        std_logger.info("This is a standard logging message (captured by TraceLog)")
        # 6. 終了処理
        print("Shutting down...")
    print(f"Test completed. Results are in '{log_file}'")

if __name__ == "__main__":
    main()
