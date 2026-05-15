#!/usr/bin/env python3

import time
import logging
import msgspec # Keep msgspec for TestData
from app.utils.log_utils.trace_log import TraceLog # Import the socket version
import pydantic

# msgspec.Struct を使ったテストデータ定義
class TestData(msgspec.Struct):
    user_id: int
    action: str
    metadata: dict[str, str]

class TestData2(pydantic.BaseModel):
    user_id: int
    action: str
    metadata: dict[str, str]

def main():
    log_file = "./test_trace.log"
    print("Initializing logger...")
    # 1. ロガーの初期化
    logger = TraceLog(log_file=log_file)
    print("Logger initialized.")

    s = (time.perf_counter()) 

    with logger:
        # 2. 各ログレベルのメソッドテスト
        print("Testing basic logging methods...")
        
        for i in range(1, 10001):
            logger.start(f"req-10{i}")
            logger.info({"message": "Informational log"}, event_message="Custom Info Event")
            logger.trace({"detail": "Low-level trace data"}, event_message="Custom Trace Event")
            logger.debug(TestData(user_id=i, action="login", metadata={"browser": "chrome"}), event_message="User Login")
            logger.warning({"issue": "Slow response detected"}, event_message="Performance Warning")
            logger.info({"message": "Informational log2"}, event_message="Custom Info Event")
            logger.trace({"detail": "Low-level trace data2"}, event_message="Custom Trace Event")
            logger.debug(TestData2(user_id=1000*100+i, action="login", metadata={"browser": "chrome"}), event_message="User Login")
            logger.warning({"issue": "Slow response detected2"}, event_message="Performance Warning")
            logger.end( {"bytes_read": 1024}) # event should be "end"
        # 6. 終了処理
        print("Shutting down...")
    
    e=(time.perf_counter() - s) * 1000.0
    print(f"Test completed. elapsed = {e}(ms).Results are in '{log_file}'")

if __name__ == "__main__":
    main()
