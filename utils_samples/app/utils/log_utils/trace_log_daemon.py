import socket
import os
import signal
import sys

class TraceLogDaemon:
    """
    独立して動作するログ収集デーモン。
    Unixドメインソケット(DGRAM)で受信し、バッファリングして高速にファイルへ書き出す。
    """
    def __init__(self, log_file: str, socket_path: str = "/tmp/tracelog.sock", buffer_limit: int = 128 * 1024):
        self.log_file = log_file
        self.socket_path = socket_path
        self.buffer_limit = buffer_limit
        self._running = True

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

        # ファイルをバイナリ・追記モードで開く
        fd = os.open(self.log_file, os.O_WRONLY | os.O_CREAT | os.O_APPEND, 0o644)

        try:
            with os.fdopen(fd, "ab", buffering=0) as f:
                buffer = []
                buffer_bytes = 0

                while self._running:
                    try:
                        # 最大 64KB のパケットを受信
                        data = sock.recv(65536)
                        if not data:
                            continue

                        line = data + b"\n"
                        buffer.append(line)
                        buffer_bytes += len(line)

                        # バッファ閾値を超えたら一括書き込み
                        if buffer_bytes >= self.buffer_limit:
                            f.write(b"".join(buffer))
                            buffer.clear()
                            buffer_bytes = 0

                    except socket.timeout:
                        # 1秒間データが来なければ、溜まっているバッファを書き出す（定期フラッシュ）
                        if buffer:
                            f.write(b"".join(buffer))
                            buffer.clear()
                            buffer_bytes = 0
                        continue
                    except BlockingIOError:
                        continue
                    except Exception as e: # Catch all other exceptions during receive/write
                        if self._running:
                            print(f"Daemon Error during receive/write: {e}", file=sys.stderr)
                        sys.stderr.flush()
                # 終了時にバッファをフラッシュ
                if buffer:
                    f.write(b"".join(buffer))
        finally:
            sock.close()
            if os.path.exists(self.socket_path):
                os.remove(self.socket_path)

if __name__ == "__main__":
    # ログファイル名を指定。テスト用にバッファを小さく(1024)設定
    log_target = "unified_trace.log"
    daemon = TraceLogDaemon(log_target, buffer_limit=1024)
    daemon.run()
