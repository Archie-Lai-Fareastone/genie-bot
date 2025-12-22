# 專案說明

- 本專案是一個基於 Python 的 Teams 聊天機器人，整合 Microsoft Foundry Agent Service 進行對話，並透過 agent 串接 Databricks Genie，能夠協助使用者進行資料分析。

[1. 套件管理](#套件管理)
[2. Bot Framework Emulator](#bot-framework-emulator)
[3. AzureCLI 驗證](#azurecli-驗證)

## 專案架構

- 專案架構圖

```
專案根目錄
├── README.md
├── requirements.txt
├── logs/       # bot 日誌
├── mlruns/     # 呼叫 genie 紀錄
├── src/
│   ├── app.py
│   ├── bot.py
│   ├── core/
│   │   ├── logger_config.py    # 日誌設定
│   │   └── settings.py         # 環境變數設定
│   ├── scripts/
│   │   └── foundry/            # foundry agent 操作
│   └── utils/
├── .env                        # 環境變數檔案
├── .env.example                # 環境變數範例檔案
```

## 套件管理

- 開發使用 Python 版本: 3.12

### 開發使用 venv 虛擬環境 (可選擇)

- 建立虛擬環境

```bash
python -m venv .venv
```

- 先啟動虛擬環境

```bash
.venv\Scripts\activate
```

- 安裝套件

1. 安裝 requirements.txt 內的套件

```bash
pip install -r requirements.txt
```

2. 安裝單一套件

```bash
pip install 套件名稱
```

- 將套件紀錄在 requirements.txt

```bash
pip freeze > requirements.txt
```

### 環境變數

- 建立 .env 檔案，確保 .env 檔案在 .gitignore 內
- 不要讓 github copilot 讀取到，只能讀取 .env.example 範例檔案

### 啟動 app

```bash
python -m uvicorn src.app:app --host 0.0.0.0 --port 8000
```

## Bot Framework Emulator

[Bot Framework Emulator](https://github.com/microsoft/botframework-emulator) 是一個桌面應用程式，允許機器人開發者在 localhost 上測試和除錯他們的機器人。

- 從[這裡](https://github.com/Microsoft/BotFramework-Emulator/releases)安裝 Bot Framework Emulator 版本 4.3.0 或更高版本

### 使用 Bot Framework Emulator 連接到機器人

- 啟動 Bot Framework Emulator
- 輸入機器人 URL：`http://localhost:3978/api/messages`

### 參考資料

- [Bot Framework 文件](https://docs.botframework.com)
- [Databricks Genie API 文件](https://docs.databricks.com/en/genie/index.html)
- [Azure Bot Service 簡介](https://docs.microsoft.com/azure/bot-service/bot-service-overview-introduction?view=azure-bot-service-4.0)

## AzureCLI 驗證

- 如果需要在 ai foundry 建立、更新、刪除 agent，使用 [Azure CLI](https://learn.microsoft.com/zh-tw/cli/azure/install-azure-cli?view=azure-cli-latest) 在本機登入 Azure

- 登入 Azure

```bash
az login --tenant <tenant_id> --use-device-code
```

- 檢查目前登入狀態

```bash
az account show
```
