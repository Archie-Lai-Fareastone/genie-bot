# 專案說明

- 本專案是一個基於 Python FastAPI 的 Teams 聊天機器人，整合 Microsoft Foundry Agent Service 進行對話，並透過 agent 串接 Databricks Genie，能夠協助使用者進行資料分析。

## 1. 專案架構

- 專案架構圖

```
專案根目錄
├── README.md
├── requirements.txt
├── logs/       # bot 日誌
├── docs/       # 專案文件
├── mlruns/     # 呼叫 genie 紀錄
├── src/
│   ├── app.py
│   ├── bot/
│   │   ├── foundry_bot.py      # 連接 Foundry Agent Service 的 Bot
│   │   └── genie_bot.py        # 連接 Databricks Genie 的 Bot
│   ├── core/
│   │   ├── logger_config.py    # 日誌設定
│   │   └── settings.py         # 集中管理環境變數設定
│   ├── scripts/
│   │   └── foundry/            # foundry project 一次性操作
│   └── utils/
├── .env                        # 環境變數檔案
├── .env.example                # 環境變數範例檔案
```

### 參考專案

- [DatabricksGenieBOT](https://github.com/carrossoni/DatabricksGenieBOT/tree/main)
- 注意事項：
  1. 參考專案使用 `aiohttp`，本專案改用 `FastAPI` 框架
  2. 參考專案架構為 webapp <--> databricks genie，本專案架構為 teams bot <--> foundry agent <--> databicks genie，呼叫對象為 Microsoft Foundry Agent Service，因此不須設定 databricks host, genie space id 等資訊。

## 2. 開發環境

- 開發使用 Python 版本: 3.12 以上

### 開發使用 venv 虛擬環境 (可選擇)

> 若不使用 venv 可直接安裝套件到全域環境

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

#### 本地開發

- 參考 .env.example 建立 .env 檔案，確保 .env 檔案在 .gitignore 內
- 不要讓 github copilot 讀取到，只能讀取 .env.example 範例檔案

#### Azure Web App

- 在 Azure Web App 設定 -> 環境變數
- 注意以下為必填，其他參考 .env.example

```
AZURE_TENANT_ID=
AZURE_CLIENT_ID=
AZURE_CLIENT_SECRET=
APP_TYPE=SingleTenant
WEBSITES_PORT=8000
```

### 啟動 app

```bash
# 本地端 (localhost:3978)
python -m src.app

# Azure Web App
python -m uvicorn src.app:app --host 0.0.0.0 --port 8000
```

## 3. 本地測試機器人

### 選項一：Bot Framework Emulator

[Bot Framework Emulator](https://github.com/microsoft/botframework-emulator) 是一個桌面應用程式，允許機器人開發者在 localhost 上測試和除錯他們的機器人。

- 從[這裡](https://github.com/Microsoft/BotFramework-Emulator/releases)安裝 Bot Framework Emulator 版本 4.3.0 或更高版本

#### 使用 Bot Framework Emulator 連接到機器人

- 啟動 Bot Framework Emulator
- 輸入機器人 URL：`http://localhost:3978/api/messages`

#### Bot Framework Adapter 設定範例

- **本地測試請傳入空字串跳過認證**，Bot Framework Emulator 不會處理認證

```python
bot_settings = BotFrameworkAdapterSettings("", "")
```

#### 參考資料

- [Bot Framework 文件](https://docs.botframework.com)
- [Databricks Genie API 文件](https://docs.databricks.com/en/genie/index.html)
- [Azure Bot Service 簡介](https://docs.microsoft.com/azure/bot-service/bot-service-overview-introduction?view=azure-bot-service-4.0)

### 選項二：Agents Playground

- 代替 Bot Framework Emulator，使用 [Agents Playground](https://learn.microsoft.com/zh-tw/microsoft-365/agents-sdk/test-with-toolkit-project?tabs=windows)
- 程式設定同 Bot Framework Emulator

#### 安裝 agentsplayground

```sh
npm install -g @microsoft/m365agentsplayground
```

#### 執行 agentsplayground

```sh
agentsplayground -e "http://localhost:3978/api/messages"

# 或直接執行
agentsplayground
```

## 4. 身分驗證

### 本地開發使用 Azure CLI 驗證

- 如果需要在 ai foundry 建立、更新、刪除 agent，使用 [Azure CLI](https://learn.microsoft.com/zh-tw/cli/azure/install-azure-cli?view=azure-cli-latest) 在本機登入 Azure

- 登入 Azure

```bash
az login --tenant <tenant_id> --use-device-code
```

- 檢查目前登入狀態

```bash
az account show
```

#### DefaultAzureCredential 使用範例

- az login 後，自動取得使用者身分登入

```python
from azure.identity import DefaultAzureCredential

# 初始化 Azure 認證
credential = DefaultAzureCredential(
    exclude_interactive_browser_credential=False,
)
# 初始化 AI Project Client
project_client = AIProjectClient(
    settings.azure_foundry["project_endpoint"], credential
)
```

### Service Principal 驗證 (部署到 Azure Web App 使用)

- 必須設定以下三個環境變數

```
AZURE_TENANT_ID=
AZURE_CLIENT_ID=
AZURE_CLIENT_SECRET=
```

- 程式碼同上，只是 DefaultAzureCredential 會自動使用 Service Principal 驗證

## 5. 部署到 Azure Web App

### 上版方法一：zip 檔案

1. 打包成 `deploy.zip` 檔案

- 只打包 src/ 目錄和 requirements.txt

```cmd
tar -a -c -f deploy.zip src requirements.txt
```

2. 使用 `az webapp deploy` 指令部署

- 檢查 webapp 名稱、resource group 是否正確

```cmd
az webapp deploy ^
    --name fet-mobilebot-webapp ^
    --resource-group fet-rag-bst-rg ^
    --src-path deploy.zip ^
    --type zip
```

### 設定啟動命令

- 寫在 web app portal 設定 -> 堆疊設定 -> 啟動命令

```sh
python3 -m uvicorn src.app:app --host 0.0.0.0 --port 8000 --workers 2 --log-level info
```
