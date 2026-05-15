import socket
import os
import signal
import sys
import threading
import queue
from typing import Optional

class TraceLogDaemon:
    """
    独立して動作するログ収集デーモン。
    Unixドメインソケット(DGRAM)で受信し、バッファリングして高速にファイルへ書き出す。
    """
    def __init__(self, log_file: str, socket_path: Optional[str] = None, buffer_limit: int = 128 * 1024):
        self.log_file = log_file
        if socket_path is None:
            socket_path = "tracelog.sock" if os.name == "nt" else "/tmp/tracelog.sock"
            
        self.socket_path = socket_path
        self.buffer_limit = buffer_limit
        self._running = True
        self._write_queue = queue.Queue()

    def _writer_thread(self):
        """ディスク書き込み専用のスレッド"""
        fd = os.open(self.log_file, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)
        with os.fdopen(fd, "ab", buffering=0) as f:
            while self._running or not self._write_queue.empty():
                try:
                    chunk = self._write_queue.get(timeout=1.0)
                    f.write(chunk)
                except queue.Empty:
                    continue

    def run(self):
        # 古いソケットのクリーンアップ
        if os.path.exists(self.socket_path):
            os.remove(self.socket_path)

        # SOCK_DGRAM (UDPのUnix版) を使用してコネクションレスで高速受信
        sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        sock.bind(self.socket_path)
        # 全てのユーザー・プロセスから書き込みを許可
        os.chmod(self.socket_path, 0o666)

        # OSレベルの受信バッファを 16MB に拡大（重要：バースト受信時の取りこぼし防止）
        # デフォルトの1MBでは10万件の超高速送信に耐えられない可能性があります
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_RCVBUF, 16 * 1024 * 1024)
        sock.settimeout(1.0)

        print(f"--- TraceLog Daemon Started ---")
        print(f"Log file: {os.path.abspath(self.log_file)}")
        print(f"Socket:   {self.socket_path}")
        sys.stdout.flush() # Ensure these prints are visible immediately

        # シグナルハンドラ
        def handle_exit(signum, frame):
            self._running = False

        signal.signal(signal.SIGINT, handle_exit)
        signal.signal(signal.SIGTERM, handle_exit)

        # 書き込みスレッド開始
        writer = threading.Thread(target=self._writer_thread)
        writer.start()

        try:
            buffer = []
            buffer_bytes = 0

            while self._running:
                try:
                    data = sock.recv(65536)
                    if not data: continue

                    line = data + b"\n"
                    buffer.append(line)
                    buffer_bytes += len(line)

                    if buffer_bytes >= self.buffer_limit:
                        self._write_queue.put(b"".join(buffer))
                        buffer.clear()
                        buffer_bytes = 0

                except socket.timeout:
                    if buffer:
                        self._write_queue.put(b"".join(buffer))
                        buffer.clear()
                        buffer_bytes = 0
                except Exception:
                    continue
        finally:
            self._running = False
            writer.join()
            sock.close()
            if os.path.exists(self.socket_path):
                os.remove(self.socket_path)

if __name__ == "__main__":
    # ログファイル名を指定。高負荷に耐えられるようバッファを調整
    log_target = "unified_trace.log"
    daemon = TraceLogDaemon(log_target, buffer_limit=128 * 1024)
    daemon.run()
