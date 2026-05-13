sequenceDiagram
    autonumber

    participant LWC as LWC UI<br>(Grid.js + Popup)
    participant SF as Salesforce Mock<br>(REST / CDC / Static)
    participant SS as Storage Server<br>(/download-request)
    participant W as Worker<br>(Chunk Upload → ContentVersion)
    participant SFO as Salesforce Objects<br>(DownloadMaster / CV / CVD)

    %% 1. LWC → Salesforce: ダウンロード要求
    LWC->>SF: POST DownloadMaster__c<br>（ファイル名・暗号化パス）
    SF->>SFO: DownloadMaster__c レコード作成
    SF-->>LWC: 受付（202）

    %% 2. Salesforce → Storage Server
    SF->>SS: POST /download-request<br>（DownloadMaster 情報）
    SS-->>SF: 202 Accepted

    %% 3. Storage Server → Worker
    SS->>W: enqueue(request)<br>（キューに投入）

    %% 4. Worker: ファイル復号 → ContentVersion 作成
    W->>W: encrypted_filepath を復号
    W->>SFO: ContentVersionData 作成（バイナリ）
    W->>SFO: ContentVersion 作成（メタデータ）

    %% 5. Worker → Salesforce: DownloadMaster 更新
    W->>SF: PATCH DownloadMaster__c<br>（Completed + ContentDocumentId）
    SF->>SFO: レコード更新

    %% 6. Salesforce → LWC: CDC 通知
    SF-->>LWC: SSE Event<br>（status=Completed）

    %% 7. LWC: UI 更新
    LWC->>LWC: Grid.js のステータス更新
