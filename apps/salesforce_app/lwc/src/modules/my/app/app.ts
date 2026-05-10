import { LightningElement, track } from 'lwc';

export default class App extends LightningElement {
    @track current = 'download';

    get isDownload() {
        return this.current === 'download';
    }

    get isAbout() {
        return this.current === 'about';
    }

    get downloadClass() {
        return this.current === 'download' ? 'active' : '';
    }

    get aboutClass() {
        return this.current === 'about' ? 'active' : '';
    }

    goDownload() {
        this.current = 'download';
    }

    goAbout() {
        this.current = 'about';
    }
}
