
# 🗄️ data（モック Salesforce データ & Storage サーバー実データ）

## 🔷 salesforce（Mock Salesforce の永続データ）

| パス                                             | 説明                                       |
| ------------------------------------------------ | ------------------------------------------------ |
| `data/salesforce/objects/ContentDocumentLink/`   | ContentDocumentLink（DownloadMaster__c との紐づけ）|
| `data/salesforce/objects/ContentVersion/`        | ContentVersion メタデータ（Title, PathOnClient など|
| `data/salesforce/objects/ContentVersionData/`    | バイナリ実体（PDF, CSV, ZIP など）   |
| `data/salesforce/objects/DownloadMasterWork__c/` | DownloadMaster のワークキュー（処理中タスク）     |
| `data/salesforce/objects/DownloadMaster__c/`     | DownloadMaster レコード（ダウンロード要求の状態管理）|

---

## 🔷 storage（Storage サーバー側の実データ & キュー）

### 📁 data/storage/data（アップロード対象の実ファイル）

| パス           | 説明           |
| -------------- | -------------- |
| `file_1.csv`   | サンプル CSV   |
| `file_10.xlsx` | サンプル Excel |
| `file_11.csv`  | サンプル CSV   |
| `file_2.txt`   | サンプル TXT   |

（※ Storage サーバーが Salesforce に送信する「元ファイル」）

---

### 📁 data/storage/logs（Storage サーバーのログ）

| パス    | 説明                                         |
| ------- | -------------------------------------------- |
| `logs/` | structlog による JSON ログが保存される |

---

### 📁 data/storage/queue（Chunk Upload のワークキュー）

| パス                | 説明                     |
| ------------------- | ------------------------ |
| `queue/accepted/`   | 受付済み（未処理）タスク |
| `queue/processing/` | 処理中タスク             |
| `queue/completed/`  | 完了タスク               |
| `queue/error/`      | エラーで停止したタスク   |

（※ JSONL 形式で 1 行 1 タスク）

