import { LightningElement, api, track } from 'lwc';

export default class DownloadPopup extends LightningElement {
    // 親コンポーネント（downloadMasterList）から制御可能にするためのプロパティ
    @api visible = false;

    @track _items = [];

    // Setterを導入して、親から新しい配列が渡されるたびに確実に検知する
    @api
    get items() {
        return this._items;
    }
    set items(value) {
        console.log('Popup received new items:', JSON.stringify(value));
        // スプレッド構文でコピーを作成し、LWCに「変更された」と強く認識させる
        this._items = value ? [...value] : [];
    }

    /**
     * 「閉じる」ボタン押下時
     * 親コンポーネントにイベントを通知して、親側で visible を false にしてもらう
     */
    close() {
        this.dispatchEvent(new CustomEvent('close'));
    }
}