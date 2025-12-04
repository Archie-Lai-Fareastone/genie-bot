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


## 環境變數
* 建立 .env 檔案，確保 .env 檔案在 .gitignore 內
* 不要讓 github copilot 讀取到: 可以建立 `.github/copilot-instructions.md` 檔案

# Bot Framework Emulator

[Bot Framework Emulator](https://github.com/microsoft/botframework-emulator) 是一個桌面應用程式，允許機器人開發者在 localhost 上測試和除錯他們的機器人。

- 從[這裡](https://github.com/Microsoft/BotFramework-Emulator/releases)安裝 Bot Framework Emulator 版本 4.3.0 或更高版本

### 使用 Bot Framework Emulator 連接到機器人

- 啟動 Bot Framework Emulator
- 輸入機器人 URL：`http://localhost:3978/api/messages`

## 參考資料

- [Bot Framework 文件](https://docs.botframework.com)
- [Databricks Genie API 文件](https://docs.databricks.com/en/genie/index.html)
- [Azure Bot Service 簡介](https://docs.microsoft.com/azure/bot-service/bot-service-overview-introduction?view=azure-bot-service-4.0)

# Azure 驗證
* 如果需要在 ai foundry 建立、刪除 agent，使用 [Azure CLI](https://learn.microsoft.com/zh-tw/cli/azure/install-azure-cli?view=azure-cli-latest) 在本機登入 Azure

* 登入 Azure
```bash
az login --use-device-code
```

* 檢查目前登入狀態
```bash
az account show
```

