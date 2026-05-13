# 🔐 ファイルパス暗号化 → Salesforce DownloadMaster__c 登録までのシーケンス図

```mermaid
sequenceDiagram
    autonumber

    participant U as User / Worker
    participant SA as storage_app<br>utils.crypto.encrypt_path()
    participant DM as storage_app<br>client.download_master_sync
    participant SF as salesforce_app<br>REST API (Mock)
    participant DB as data/salesforce/objects<br>DownloadMaster__c/*.json

    %% 1. 元ファイルの選択
    U->>DM: 対象ファイルのメタ情報を生成<br>(filename, ext, plain_path)

    %% 2. 暗号化
    DM->>SA: encrypt_path(plain_path)
    SA-->>DM: encrypted_filepath (Fernet)

    %% 3. DownloadMaster__c レコード生成
    DM->>SF: POST /services/data/.../sobjects/DownloadMaster__c<br>{ filename, filename_disp, encrypted_filepath, ext }
    SF->>DB: JSON ファイルとして保存
    SF-->>DM: { id: "a01xxxx..." }

    %% 4. 完了
    DM-->>U: DownloadMaster__c レコードIDを返す
```

---

# 📝 補足説明

## 🔐 1. ファイルパスの暗号化（storage_app/utils/crypto.py）
- AES-GCM で **絶対パスを暗号化**
- Salesforce 側には **復号できない文字列**だけ渡す
- 復号は storage_app 側だけが可能

例：
```python
encrypted = encrypt_path("data/storage/data/file_1.csv")
```

---

## 📤 2. DownloadMaster__c レコード作成（storage_app/client/download_master_sync.py）
暗号化済みパスを含む JSON を Salesforce Mock API に送信：

```json
{
  "filename": "file_1.csv",
  "filename_disp": "file_1.csv",
  "encrypted_filepath": "gAAAAABl....",
  "ext": "csv"
}
```

---

## 🗂 3. Salesforce 側で JSON 保存（data/salesforce/objects/DownloadMaster__c）
- 1 レコード = 1 JSON ファイル
- LWC のダウンロード画面はこの JSON を読み込んで一覧表示

