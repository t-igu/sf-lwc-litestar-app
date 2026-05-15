import importlib
import logging
import multiprocessing as mp
import queue
import os
import sys
import time
import traceback
from typing import Any, Optional, Union

import msgspec
import structlog
from structlog.types import Processor, EventDict

# 独自のTRACEレベルを定義 (DEBUG: 10 より下の 5)
TRACE_LEVEL_NUM = 5

# structlog の内部マッピングに TRACE を登録し、KeyError と TypeError を回避する
try:
    # Pylance の PrivateImportUsage を回避するため動的にインポートして操作
    _sn = importlib.import_module("structlog._native")
    getattr(_sn, "LEVEL_TO_NAME")[TRACE_LEVEL_NUM] = "trace"
    getattr(_sn, "NAME_TO_LEVEL")["trace"] = TRACE_LEVEL_NUM
except (ImportError, AttributeError, TypeError):
    # structlog のバージョンにより構造が異なる場合のフォールバック
    pass

logging.addLevelName(TRACE_LEVEL_NUM, "TRACE")

class TraceLogWriter:
    """別プロセスで実行される書き込み専用クラス"""
    @staticmethod
    def run(queue: mp.Queue, file_path: str, buffer_limit: int = 64 * 1024):
        # 高速化のため os.open を使用し、バイナリモードで追記
        fd = os.open(file_path, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
        with os.fdopen(fd, "ab", buffering=0) as f:
            buffer = []
            buffer_bytes = 0
            while True:
                try:
                    item = queue.get()
                    if item is None:  # 終了シグナル
                        if buffer:
                            f.write(b"".join(buffer))
                        break
                    
                    line = item + b"\n"
                    buffer.append(line)
                    buffer_bytes += len(line)

                    # 設定したバッファサイズを超えたら一括書き込み
                    if buffer_bytes >= buffer_limit:
                        f.write(b"".join(buffer))
                        buffer.clear()
                        buffer_bytes = 0

                except KeyboardInterrupt:
                    break
                except Exception:
                    continue

class TraceLog:
    def __init__(self, log_file: str, service_name: str = "app", queue_size: int = 100_000):
        self._service_name = service_name
        self._start_times: dict[str, float] = {}
        self._encoder = msgspec.json.Encoder()
        
        # 非同期書き込み用キュー
        self._ctx = mp.get_context("fork" if os.name != "nt" else "spawn")
        self._queue = self._ctx.Queue(maxsize=queue_size)
        
        # 書き込みプロセス開始
        self._writer = self._ctx.Process(
            target=TraceLogWriter.run,
            args=(self._queue, log_file),
            daemon=False
        )
        self._writer.start()

        # structlog の設定
        self._setup_structlog()
        self._logger = structlog.get_logger()
        
        # FastAPI / HTTPX (標準logging) の統合
        self._integrate_standard_logging()

    _STR_TO_LEVEL = {
        "trace": TRACE_LEVEL_NUM,
        "debug": logging.DEBUG,
        "info": logging.INFO,
        "warning": logging.WARNING,
        "error": logging.ERROR,
        "critical": logging.CRITICAL,
    }

    def _setup_structlog(self):
        """structlogのパイプライン設定"""
        processors: list[Processor] = [
            structlog.contextvars.merge_contextvars,
            structlog.processors.add_log_level,
            structlog.processors.TimeStamper(fmt="iso", utc=True),
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            self._queue_processor, # 自作プロセッサでQueueへ流す
        ]
        
        structlog.configure(
            processors=processors,
            logger_factory=structlog.PrintLoggerFactory(), # 内部で使わないので軽量なものを指定
            cache_logger_on_first_use=True,
        )

    def _queue_processor(self, logger: Any, method_name: str, event_dict: EventDict) -> Any:
        """structlog のイベントを JSON 化して Queue に入れる"""
        event_dict["service"] = self._service_name
        try:
            # msgspecでバイト列にエンコード
            self._queue.put_nowait(self._encoder.encode(event_dict))
        except queue.Full:
            # キューが満杯の場合はドロップ（パフォーマンス優先）
            pass
        except Exception:
            pass
        
        # structlog 自体の後続処理（コンソール出力等）は不要なため DropPickle 的な挙動
        raise structlog.DropEvent

    def _integrate_standard_logging(self):
        """FastAPIやhttpxの標準ログをキャッチして structlog に流す"""
        class InterceptHandler(logging.Handler):
            def emit(self, record):
                # ログレベルの取得
                level = record.levelno
                kwargs = {
                    "event": record.getMessage(),
                    "logger_name": record.name,
                    "process_id": record.process,
                    "thread_name": record.threadName,
                }
                event = kwargs.pop("event")
                if record.exc_info:
                    kwargs["exc_info"] = record.exc_info

                structlog.get_logger("stdlib").log(level, event, **kwargs)

        # 全てのハンドラを削除して入れ替え
        root_logger = logging.getLogger()
        for h in root_logger.handlers[:]:
            root_logger.removeHandler(h)
        root_logger.addHandler(InterceptHandler())
        root_logger.setLevel(TRACE_LEVEL_NUM)

    @classmethod
    def _convert_data(cls, data: Any) -> Any:
        """msgspec, pydantic, dict を msgspec でシリアライズ可能な形式に変換"""
        if data is None:
            return {}
        if isinstance(data, dict):
            return data
        # msgspec.Struct, Pydantic, dataclasses などを高速に dict/list へ変換
        try:
            return msgspec.to_builtins(data)
        except Exception:
            return str(data)


    def _log(self, level: str, request_id: str, data: Any, event_message: Optional[str] = None, **kwargs):
        """structlogを呼び出す共通メソッド (整数レベルを使用して TypeError を回避)"""
        level_lower = level.lower()
        # 文字列から整数レベルへ変換。未定義なら INFO(20)
        level_int = self._STR_TO_LEVEL.get(level_lower, logging.INFO)
        # event_message が指定されていない場合は request_id を event 名として使用
        self._logger.log(level_int, event_message or request_id, request_id=request_id, data=self._convert_data(data), **kwargs)

    def debug(self, request_id: str, data: Any = None, event_message: Optional[str] = None):
        self._log("debug", request_id, data, event_message=event_message)

    def error(self, request_id: str, data: Any = None, exc_info: bool = False, event_message: Optional[str] = None):
        self._log("error", request_id, data, exc_info=exc_info, event_message=event_message)

    def trace(self, request_id: str, data: Any = None, event_message: Optional[str] = None):
        """カスタムレベル TRACE でのログ出力"""
        self._log("trace", request_id, data, event_message=event_message)

    def info(self, request_id: str, data: Any = None, event_message: Optional[str] = None):
        self._log("info", request_id, data, event_message=event_message)

    def warning(self, request_id: str, data: Any = None, event_message: Optional[str] = None):
        self._log("warning", request_id, data, event_message=event_message)

    def start(self, request_id: str, data: Any = None, event_message: Optional[str] = None, level: str="info"):
        """計測開始ログ"""
        self._start_times[request_id] = time.perf_counter()
        self._log(level, request_id, data, event_message=event_message or "start")

    def end(self, request_id: str, data: Any = None, event_message: Optional[str] = None, level: str="info", **kwargs):
        """計測終了ログ。経過時間(elapsed_ms)を自動計算"""
        start_time = self._start_times.pop(request_id, None)
        elapsed = None
        if start_time is not None:
            elapsed = (time.perf_counter() - start_time) * 1000.0
        self._log(level, request_id, data, event_message=event_message or "end", elapsed_ms=elapsed)

    def shutdown(self):
        """ロガーの終了処理。未出力のログをフラッシュする"""
        if self._queue:
            try:
                self._queue.put(None, timeout=2)
                # Writerプロセスがバッファを書き終えるのを待つ
                max_wait = 5.0
                start_wait = time.time()
                while self._writer.is_alive():
                    if time.time() - start_wait > max_wait:
                        break
                    time.sleep(0.1)
            except Exception:
                self._writer.terminate()
