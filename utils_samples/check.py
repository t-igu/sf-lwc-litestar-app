import json
from collections import defaultdict


def analyze_log(file_path):
    stats = defaultdict(set)
    errors = []
    total_lines = 0

    print(f"Analyzing {file_path}...")

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            total_lines += 1
            try:
                log = json.loads(line)
                rid = log.get("request_id")
                event = log.get("event")
                
                if rid:
                    stats[rid].add(event)
                
                if log.get("level") == "error":
                    errors.append(log)
            except Exception as e:
                print(f"Malformed line at {total_lines}: {e} - Line: {line.strip()}")

    # 集計
    total_requests = len(stats)
    completed = 0
    successful_requests = 0
    error_requests = 0
    missing_end = []
    total_elapsed_ms = 0
    elapsed_count = 0
    
    # 終了とみなすイベント名のセット
    termination_events = {"end", "request_exception", "middleware_exception", "request_failed"}

    for rid, events in stats.items():
        # 終了イベントが一つでもあれば完了とみなす
        has_termination_event = bool(events & termination_events)

        if "start" in events and has_termination_event:
            completed += 1
            # ログレベルがerrorの終了イベントがあればエラーリクエスト
            if any(e in events for e in {"request_exception", "request_failed"}):
                error_requests += 1
            else:
                successful_requests += 1
            
            # elapsed_ms を集計 (最後の終了イベントから取得)
            for line in reversed(list(open(file_path, "r", encoding="utf-8"))): # 効率は悪いが、最後のイベントを探す
                try:
                    log = json.loads(line)
                    if log.get("request_id") == rid and log.get("event") in termination_events and "elapsed_ms" in log:
                        total_elapsed_ms += log["elapsed_ms"]
                        elapsed_count += 1
                        break
                except Exception:
                    pass
        elif "start" in events:
            # 最後の数件は処理中の可能性があるが、高負荷時に消えた場合は漏れ
            missing_end.append(rid)

    print("-" * 30)
    print(f"Total Log Lines:  {total_lines}")
    print(f"Unique Requests: {total_requests}")
    print(f"Completed OK:    {completed}")
    print(f"  - Successful:  {successful_requests}")
    print(f"  - Errors:      {error_requests}")
    print(f"Missing End:     {len(missing_end)}")
    print(f"Error Logs:      {len(errors)}")
    print("-" * 30)

    if missing_end:
        print("First 5 Missing IDs:", missing_end[:5])
    
    if elapsed_count > 0:
        print(f"Average Elapsed Time (Completed Requests): {total_elapsed_ms / elapsed_count:.2f} ms")

    if len(stats) > 0 and len(missing_end) == 0:
        print("Result: Success! No log omissions detected.")
    else:
        print("Result: Some logs might be missing or the app was stopped mid-request.")

if __name__ == "__main__":
    # 実際のログファイルパスを指定してください
    analyze_log(r"c:\workspace\python\github_projects\sf-lwc-litestar-app\utils_samples\fastapi_queue.log")
