# Local Async File Download Demo

Salesforce 互換 API を用いた **非同期ファイルダウンロード処理** を  
ローカル環境で完全再現するデモプロジェクトです。

- Salesforce® は一切不要（完全ローカルのモック環境）
- LWC → Apex → Storage → Worker → Mock Salesforce → CDC の一連の流れを再現
- Chunk Upload / 非同期処理 / 状態管理 / ログ基盤を統合

詳細な技術ドキュメントは `/docs` に分割されています。

---

## 🚀 Quick Start

### 1. Javascript Build

```bash
cd apps\salesforce_app\lwc
npm install
npm run build
```

### 2. vitaualenv setup

for windows:

```bash
cd apps
python -m venv .venv
.venv/bin/activate
pip install -r requirements.txt
cd ..
```

### 3. run server

```bash
run.bat
```

### 4. create directories and create sample data

for windows:

```bash
python setup.py
python setup_send_data.py
```

### 3. Open UI

```
http://localhost:8000/index.html
```

---


## ⚠️ Note

本プロジェクトは Salesforce® の API を使用していません。  
すべてローカルで動作する **互換 API を持つモックサーバー**です。

---

## 📄 License

MIT License  


