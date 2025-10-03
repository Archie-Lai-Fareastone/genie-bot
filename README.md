# 套件管理

## 使用 venv 虛擬環境

* 建立虛擬環境
```bash
python -m venv .venv
```

* 啟動虛擬環境
```bash
.venv\Scripts\activate
```

* 安裝套件: **先啟動虛擬環境後，再執行以下指令**
1. 安裝 requirements.txt 內的套件
```bash
pip install -r requirements.txt
```
2. 安裝單一套件
```bash
pip install 套件名稱
```

* 將套件紀錄在 requirements.txt
```bash
pip freeze > requirements.txt
```