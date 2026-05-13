# 📁 プロジェクト構成一覧（README 用）

## 🧩 apps（共通モジュール）

| パス               | 説明                         |
| ------------------ | ---------------------------- |
| `apps/__init__.py` | apps パッケージ初期化        |
| `apps/const.py`    | 共通定数（パス、設定値など） |

---

# 🏢 salesforce_app（LWC + Mock Salesforce API）

## 🔷 LWC フロントエンド（apps/salesforce_app/lwc/src）

| パス                                          | 説明                               |
| --------------------------------------------- | ---------------------------------- |
| `index.html`                                  | LWC OSS のエントリ HTML            |
| `index.js`                                    | LWC アプリ起動スクリプト           |
| `modules/my/app/app.html`                     | メイン画面の HTML テンプレート     |
| `modules/my/app/app.css`                      | メイン画面のスタイル               |
| `modules/my/app/app.ts`                       | メイン画面のロジック（TypeScript） |
| `modules/my/download/download.html`           | ダウンロード一覧画面のテンプレート |
| `modules/my/download/download.css`            | ダウンロード一覧画面のスタイル     |
| `modules/my/download/download.js`             | ダウンロード一覧画面のロジック     |
| `modules/my/downloadPopup/downloadPopup.html` | ダウンロード詳細ポップアップ       |
| `modules/my/downloadPopup/downloadPopup.css`  | ポップアップのスタイル             |
| `modules/my/downloadPopup/downloadPopup.js`   | ポップアップのロジック             |
| `public/gridjs/gridjs.js`                     | Grid.js 本体（ESM）                |
| `public/gridjs/gridjs.umd.js`                 | Grid.js UMD 版                     |
| `public/gridjs/theme/mermaid.min.css`         | Grid.js 用テーマ                   |

---

## 🔷 Mock Salesforce Server（apps/salesforce_app/server）

| パス                                       | 説明                                |
| ------------------------------------------ | ----------------------------------- |
| `server/__init__.py`                       | パッケージ初期化                    |
| `server/main.py`                           | Litestar アプリのエントリポイント   |
| `server/models.py`                         | msgspec.Struct による共通モデル定義 |
| `server/routers/apex_router.py`            | Apex REST 風 API のモック           |
| `server/routers/auth_router.py`            | OAuth / 認証モック                  |
| `server/routers/cdc_router.py`             | Change Data Capture モック（SSE）   |
| `server/routers/composite_router.py`       | Composite API モック                |
| `server/routers/lwc_router.py`             | LWC 静的ファイル配信                |
| `server/routers/restapi_router.py`         | Salesforce REST API モック          |
| `server/sobjects/base.py`                  | SObject の基底クラス                |
| `server/sobjects/content_document_link.py` | ContentDocumentLink モック          |
| `server/sobjects/content_version.py`       | ContentVersion モック               |
| `server/sobjects/content_version_data.py`  | バイナリデータ管理                  |
| `server/sobjects/download_master.py`       | DownloadMaster__c モック            |

---

# 📦 storage_app（Chunk Upload 実行側）

## 🔷 client（Salesforce 側と通信するクライアント）

| パス                             | 説明                                 |
| -------------------------------- | ------------------------------------ |
| `client/auth.py`                 | 認証トークン管理                     |
| `client/http_client.py`          | httpx ベースの共通 HTTP クライアント |
| `client/token.py`                | JWT / アクセストークン生成           |
| `client/version_data.py`         | ContentVersionData 送信処理          |
| `client/download_master_sync.py` | DownloadMaster__c の同期処理         |
| `client/notify.py`               | 完了通知処理                         |
| `client/worker_executor.py`      | Worker 実行エントリ                  |
| `client/worker_loop.py`          | キュー監視ループ                     |

---

## 🔷 models（storage_app 側の msgspec モデル）

| パス               | 説明                                              |
| ------------------ | ------------------------------------------------- |
| `models/models.py` | schema.json → create_models.py で生成されたモデル |

---

## 🔷 server（storage_server）

| パス                                | 説明                              |
| ----------------------------------- | --------------------------------- |
| `server/main.py`                    | Litestar アプリのエントリポイント |
| `server/routers/download_router.py` | ダウンロード要求受付 API          |

---

## 🔷 utils（共通ユーティリティ）

| パス                         | 説明                               |
| ---------------------------- | ---------------------------------- |
| `utils/crypto.py`            | AES-GCM 暗号化/復号                |
| `utils/logging_config.py`    | structlog 設定                     |
| `utils/logging_context.py`   | contextvars による request_id 管理 |
| `utils/logging_decorator.py` | trace_action デコレータ            |
| `utils/logging_utils.py`     | ログ整形ユーティリティ             |
| `utils/queue_manager.py`     | JSONL キュー管理                   |

---

# 📊 log_viewer（ログ閲覧ツール）

| パス                                        | 説明                                |
| ------------------------------------------- | ----------------------------------- |
| `log_viewer/log_viewer.py`                  | DuckDB + AG Grid のログビューア本体 |
| `log_viewer/log_viewer.bat`                 | Windows 用起動スクリプト            |
| `log_viewer/templates/requirements_dev.txt` | log_viewer 用の依存ライブラリ       |
| `log_viewer/run.bat`                        | ログビューア起動バッチ              |
| `log_viewer/setup.py`                       | ログビューアセットアップ            |
| `log_viewer/setup_send_data.py`             | ログ送信用スクリプト                |

---

