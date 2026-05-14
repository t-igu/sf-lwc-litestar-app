from __future__ import annotations

import logging
import os
import signal
import threading
import time
from pathlib import Path
from typing import Any, Callable, Optional

import tomllib
from watchdog.events import FileSystemEventHandler, FileModifiedEvent
from watchdog.observers import Observer

log = logging.getLogger(__name__)


class ConfigLoadError(Exception):
    """設定ファイルの読み込みに失敗したときに投げる例外。"""
    pass


def _load_toml(path: Path) -> dict[str, Any]:
    """
    TOML ファイルを読み込んで dict にして返す。
    - ファイルが存在しない
    - TOML の構文が壊れている
    などの場合は ConfigLoadError を投げる。
    """
    if not path.exists():
        raise ConfigLoadError(f"Config file not found: {path}")

    try:
        with path.open("rb") as f:
            return tomllib.load(f)
    except Exception as e:
        raise ConfigLoadError(f"Failed to load TOML: {e}") from e


class HotConfig:
    """
    Linux 向けの「設定ファイルホットリロード」クラス。

    特徴：
    - 設定ファイル(config.toml)を監視し、変更されたら即時反映
    - アプリ側は常にメモリ上の dict を読むので高速
    - TOML が壊れていたら前回の設定を維持（ロールバック）
    - inotify を使うので CPU 負荷はほぼゼロ
    - SIGINT/SIGTERM を受けたら自動で監視スレッドを停止（安全）
    """

    def __init__(
        self,
        path: Path,
        *,
        on_update: Optional[Callable[[dict[str, Any]], None]] = None,
        debounce_sec: float = 0.1,
    ) -> None:
        """
        :param path: 監視する設定ファイルのパス
        :param on_update: 設定更新時に呼ばれるコールバック（任意）
        :param debounce_sec: 保存時の連続イベントをまとめるためのデバウンス秒数
        """
        self._path = path
        self._on_update = on_update
        self._debounce_sec = debounce_sec

        # 設定の読み書きを守るためのロック
        self._lock = threading.RLock()

        # 現在の設定（dict）
        self._config: Optional[dict[str, Any]] = None

        # watchdog の監視スレッド
        self._observer: Optional[Observer] = None

        # stop() が呼ばれたかどうか
        self._stop_event = threading.Event()

        # デバウンス用のタイムスタンプ
        self._last_event_ts = 0.0

        # SIGINT/SIGTERM を受けたら自動で stop() する
        self._register_signal_handlers()

        # 初回ロード（ここで TOML が壊れていたら例外を投げてアプリ起動を止める）
        self._reload(initial=True)

        # ファイル監視を開始
        self._start_watcher()

    # -----------------------------
    # Public API（アプリ側が使う部分）
    # -----------------------------
    def get(self) -> dict[str, Any]:
        """
        現在の設定 dict を返す。
        - 常にメモリ上の値を返すので高速
        - スレッドセーフ
        """
        with self._lock:
            if self._config is None:
                raise RuntimeError("Config not loaded")
            return self._config

    def stop(self) -> None:
        """
        設定ファイル監視スレッドを停止する。
        - FastAPI の lifespan や worker の finally で呼ぶ
        - 呼ばなくてもプロセス終了時にスレッドは死ぬが、
          本番では安全のため stop() を呼ぶのがベスト
        """
        self._stop_event.set()

        if self._observer is not None:
            self._observer.stop()
            self._observer.join(timeout=5)

        log.info("HotConfig watcher stopped")

    # -----------------------------
    # Internal（内部処理）
    # -----------------------------
    def _reload(self, *, initial: bool = False) -> None:
        """
        設定ファイルを読み直してメモリ上の設定を更新する。
        - TOML が壊れていたら前回の設定を維持（ロールバック）
        """
        try:
            new_conf = _load_toml(self._path)

            # 読み込み成功 → 設定を更新
            with self._lock:
                self._config = new_conf

            if not initial:
                log.info("Config reloaded from %s", self._path)

            # 更新時のコールバック
            if self._on_update:
                try:
                    self._on_update(new_conf)
                except Exception:
                    log.exception("on_update callback failed")

        except Exception as e:
            if initial:
                # 初回ロード失敗は致命的 → アプリ起動を止める
                log.error("Initial config load failed: %s", e)
                raise
            else:
                # 2 回目以降はロールバック
                log.error("Config reload failed, keeping previous config: %s", e)

    def _start_watcher(self) -> None:
        """
        watchdog を使って設定ファイルの変更を監視する。
        Linux では inotify を使うので非常に軽量。
        """

        class Handler(FileSystemEventHandler):
            """設定ファイルが変更されたときに呼ばれるイベントハンドラ。"""

            def __init__(self, outer: HotConfig) -> None:
                self._outer = outer

            def on_modified(self, event: FileModifiedEvent) -> None:
                # stop() が呼ばれていたら何もしない
                if self._outer._stop_event.is_set():
                    return

                # 対象ファイル以外の変更は無視
                if Path(event.src_path) != self._outer._path:
                    return

                # デバウンス処理（VSCode などは保存時に複数イベントが飛ぶ）
                now = time.time()
                if now - self._outer._last_event_ts < self._outer._debounce_sec:
                    return
                self._outer._last_event_ts = now

                log.info("Config file modified: %s", event.src_path)
                self._outer._reload(initial=False)

        observer = Observer()
        handler = Handler(self)

        # 設定ファイルのあるディレクトリを監視
        observer.schedule(handler, self._path.parent.as_posix(), recursive=False)

        # デーモンスレッドとして起動（プロセス終了時に自動で死ぬ）
        observer.daemon = True
        observer.start()

        self._observer = observer
        log.info("Started config watcher on %s", self._path)

    def _register_signal_handlers(self):
        """
        SIGINT（Ctrl+C）や SIGTERM（systemd/docker stop）を受けたら
        自動で stop() を呼ぶ。
        - 本番運用で安全に終了するための仕組み
        """

        def handler(signum, frame):
            log.info(f"Received signal {signum}, stopping HotConfig...")

            try:
                self.stop()
            except Exception:
                log.exception("Failed to stop HotConfig cleanly")

            # デフォルトのシグナル動作に戻して再送 → プロセス終了
            signal.signal(signum, signal.SIG_DFL)
            os.kill(os.getpid(), signum)

        # Ctrl+C / systemd stop / docker stop に対応
        for sig in (signal.SIGINT, signal.SIGTERM):
            signal.signal(sig, handler)
