import { LightningElement, track } from 'lwc';

export default class Download extends LightningElement {
    @track records = [];
    @track showPopup = false;
    @track selectedFiles = [];

    schema = null;
    gridInitialized = false;
    sseMap = new Map();

    connectedCallback() {
        this.loadSchema().then(() => this.handleRefresh());
    }

    disconnectedCallback() {
        // 画面終了時にすべての SSE を閉じる
        for (const es of this.sseMap.values()) {
            if (es && typeof es.close === "function") {
                es.close();
            }
        }
        this.sseMap.clear();
    }
    async loadSchema() {
        const response = await fetch('/apex/schema');
        const data = await response.json();
        this.schema = data.models?.DownloadMaster__c?.fields || {};
    }

    async handleRefresh() {
        const response = await fetch('/apex/api/download-masters');
        const data = await response.json();

        this.records = data.map(record => {
            const safeRecord = { ...record };
            safeRecord.id = record.id || record.Id;
            safeRecord.filename_disp = record.filename_disp;
            safeRecord.extension = record.extension;
            safeRecord.status = record.status;
            safeRecord.requested = false;
            safeRecord.checked = false;      // ★ ここで初期化
            return safeRecord;
        });

        this.renderGrid();
    }

    renderGrid() {
        if (this.gridInitialized) return;
        this.gridInitialized = true;

        const gridRoot = this.template.querySelector('#grid');
        if (!gridRoot) return;

        const gridData = this.records.map(r => [
            r.checked,
            r.filename_disp,
            r.extension,
            r.status,
            r.id
        ]);

        new window.gridjs.Grid({
            columns: [
                {
                    name: "選択",
                    width: "60px",
                    formatter: (cell, row) => {
                        return gridjs.html(`
                            <input type="checkbox" class="row-check" data-id="${row.cells[4].data}">
                        `);
                    }
                },
                { name: "ファイル名", width: "40%" },
                { name: "拡張子", width: "10%" },
                { name: "ステータス", width: "20%" },
                { name: "ID", hidden: true }
            ],
            data: gridData,
            search: true,
            sort: true,
            pagination: { enabled: true, limit: 10 }
        }).render(gridRoot);

        // ★ this を壊さない
        gridRoot.addEventListener('change', (e) => this.handleGridCheckboxChange(e));
    }

    handleGridCheckboxChange(e) {
        if (!e.target.classList.contains('row-check')) return;

        const id = e.target.dataset.id;
        const checked = e.target.checked;

        const newRecords = JSON.parse(JSON.stringify(this.records));

        this.records = newRecords.map(r =>
            r.id == id ? { ...r, checked } : r
        );

        console.log("records", this.records);
    }

    async handleDownloadSelected() {
        // 1. チェックされたレコードだけ抽出
        const targets = this.records.filter(record => record.checked);

        if (targets.length === 0) {
            alert("ファイルが選択されていません");
            return;
        }

        // 2. ポップアップに表示する初期データ
        this.selectedFiles = targets.map(t => ({
            id: t.id,
            name: t.filename_disp,
            status: '準備中...'
        }));

        this.showPopup = true;
        await Promise.resolve(); // popup の描画待ち

        // 3. Litestar に送る ID リスト
        const fileIds = targets.map(t => t.id);

        try {
            const response = await fetch('/apex/download-request', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ file_ids: fileIds })
            });

            if (!response.ok) {
                throw new Error(`HTTP ${response.status}`);
            }

            const data = await response.json();
            console.log("download-request response:", data);

            // ★ Litestar は master_id を 1 つ返す
            const masterId = data.master_id;

            // 4. 全ターゲットに masterId をセット
            targets.forEach(record => {
                record.masterId = masterId;
                record.requested = true;

                // ★ Litestar 版のステータス監視（SSE or polling）
                this.subscribeCdc(record);
            });

        } catch (error) {
            console.error('Download Request Failed', error);
            targets.forEach(t => this.updateSelectedFileStatus(t.id, 'エラー ❌'));
        }
    }
    subscribeCdc(record) {
        const id = record.id;

        // 既存の SSE を閉じる
        const oldEs = this.sseMap.get(id);
        if (oldEs && typeof oldEs.close === "function") {
            oldEs.close();
        }

        // 新しい SSE
        const es = new EventSource(`/services/data/v60.0/cdc/stream/${id}`);
        this.sseMap.set(id, es);

        console.log("SSE connected:", id);
        es.onmessage = (event) => {
            const data = JSON.parse(event.data);
            console.log("SSE event:", data);

            if (data.status === "Completed" || data.status === "completed") {
                this.updateSelectedFileStatus(record.id, "完了 ✅");

                const docId = data.ContentDocumentId__c || data.content_document_id;

                if (docId) {
                    this.triggerBrowserDownload(
                        docId,
                        record.filename_disp
                    );
                }

                es.close();
            }
        };

        es.onerror = (err) => {
            console.error("SSE error:", err);
            es.close();
        };
    }


    async monitorStatus(record) {
        let retryCount = 0;
        const MAX_RETRIES = 30; // 2秒間隔 × 30回 = 最大60秒間でタイムアウト

        const poll = async () => {
            try {
                // 1. タイムアウト判定
                if (retryCount >= MAX_RETRIES) {
                    console.warn(`Polling timed out for ${record.id}`);
                    this.updateSelectedFileStatus(record.id, 'タイムアウト ❌');
                    return;
                }
                retryCount++;

                const response = await fetch(`/services/data/v60.0/cdc/stream?id=${record.id}`);
                const rawText = await response.text();

                console.log(`Polling attempt ${retryCount} for ${record.id}`, { rawText });

                // レスポンスが空（イベントがまだサーバーに届いていない）場合は2秒後に再試行
                if (!rawText || rawText.trim() === '') {
                    setTimeout(poll, 2000);
                    return;
                }

                // サーバーからの通知に「完了」や「069(ContentDocumentIdの頭)」が含まれているか
                const isFinished = rawText.includes('完了') ||
                    rawText.includes('\\u5b8c\\u4e86') ||
                    rawText.includes('069');
                const isTarget = rawText.includes(String(record.id || '').replace('DM-', ''));

                if (isFinished && isTarget) {
                    console.log('Match found! Updating UI to complete.');
                    this.updateSelectedFileStatus(record.id, '完了 ✅');

                    // ファイルIDの抽出とダウンロードの実行
                    const match = rawText.match(/"ContentDocumentId__c":\s*"([^"]+)"/);
                    if (match && match[1]) {
                        const fileId = match[1];
                        this.triggerBrowserDownload(fileId, record.filename_disp);
                    }
                    return; // 完了したら終了
                }
                // まだ完了していなければ 2秒後に再試行
                setTimeout(poll, 2000);
            } catch (err) {
                console.error('Status monitor error', err);
            }
        };
        poll();
    }

    updateSelectedFileStatus(recordId, status) {
        const targetId = String(recordId).trim();
        console.log(`Updating UI: Record ${targetId} -> ${status}`);

        // 1. メインリスト(this.records)側のステータスを更新
        this.records = this.records.map(item => {
            if (String(item.id).trim() === targetId) {
                return { ...item, status: status };
            }
            return item;
        });

        // 2. ポップアップ(selectedFiles)側のステータスを更新
        // indexを直接見つけることで確実にマッチさせる
        const newSelectedFiles = this.selectedFiles.map(item => {
            // 両方のID（idプロパティとIdプロパティ）を念のためチェック
            const itemId = String(item.id || item.Id || '').trim();
            if (itemId === targetId) {
                return { ...item, status: status };
            }
            return item;
        });

        // 配列の参照を完全に新しくして、子コンポーネントへの変更通知を強制する
        this.selectedFiles = [...newSelectedFiles];
        this.renderGrid();
    }

    // ブラウザのダウンロード機能をキックする
    triggerBrowserDownload(fileId, fileName) {
        // 本来はSalesforceのサーブレットURLだが、ここではMockエンドポイントを想定
        const downloadUrl = `/sfc/servlet.shepherd/version/download/${fileId}?asNamesFile=${fileName}`;
        const link = document.createElement('a');
        link.href = downloadUrl;
        link.download = fileName;
        document.body.appendChild(link); // DOMに一時的に追加
        link.click();
        document.body.removeChild(link); // 実行後に削除
    }

    handleBack() {
        // Homeに戻るロジック（必要に応じて実装）
    }

    handlePopupClose() {
        this.showPopup = false;
    }

}

