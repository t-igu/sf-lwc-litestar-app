import { LightningElement } from 'lwc';

export default class About extends LightningElement {
    handleBack() {
        // カスタムイベントを発行して親コンポーネントに遷移を伝える
        this.dispatchEvent(new CustomEvent('navigate', {
            detail: 'home'
        }));
    }
}