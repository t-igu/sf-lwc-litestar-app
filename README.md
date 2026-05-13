# Local Async File Download Demo

Salesforce 互換 API を用いた **非同期ファイルダウンロード処理** をローカル環境で完全再現するデモプロジェクトです。

- LWC → Apex → Storage → Worker → Mock Salesforce → CDC の一連の流れを再現

シーケンス図

[flow](docs\flow_0.md)


![](docs\images\flow_1.drawio.svg)

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

## Open UI

```
http://localhost:8000/index.html
```

---

## details

[module list](docs/module_list.md)

[directory](docs/directories.md)


## ⚠️ Note

本プロジェクトは Salesforce® の API を使用していません。  
すべてローカルで動作する **互換 API を持つモックサーバー**です。

---

## 📄 License

MIT License  


