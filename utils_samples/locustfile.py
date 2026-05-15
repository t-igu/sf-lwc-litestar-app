import uuid
from locust import HttpUser, task, between

class ApiUser(HttpUser):
    # リクエスト間の待ち時間（秒）。負荷を最大化したい場合は 0 に設定
    wait_time = between(0.1, 0.5)
    wait_time = between(0.01, 0.05)

    # @task(10)
    @task
    def test_index(self):
        """
        正常系のパスに負荷をかけます。
        TraceLoggingMiddleware によって start/end ログが出力されます。
        """
        request_id = str(uuid.uuid4())
        response = self.client.get(
            "/",
            headers={"X-Request-ID": request_id},
            name="GET / (Normal)"
        )
        if response.status_code == 404:
            print(f"DEBUG: 404 Not Found at {response.url}")

    # @task(1)
    # def test_error(self):
    #     """
    #     エラー系のパスに負荷をかけます。
    #     ミドルウェアの catch 句による error ログの出力をテストします。
    #     """
    #     request_id = str(uuid.uuid4())
    #     # 500エラーが返ることを期待しているため catch_response=True
    #     with self.client.get(
    #         "/error",
    #         headers={"X-Request-ID": request_id},
    #         name="GET /error (Exception)",
    #         catch_response=True
    #     ) as response:
    #         if response.status_code == 500:
    #             response.success()
    #         else:
    #             response.failure(f"Unexpected status code: {response.status_code}")
        self.client.get("/", name="GET / (Normal)")