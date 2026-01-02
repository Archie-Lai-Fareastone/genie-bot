# 部屬紀錄

> 2025/12/22 ~ 2025/12/24
> Author: Archie Lai

## A. 部屬環境設定

- 重點：網路接通，給 MobileAgent 權限

### 1. Azure 資源建立

> 注意事項：確保網路接通，MobileAgent 身分被建立  
> tenant: `FarEasTone Telecommunications Co., Ltd`  
> subscription: `IDTT-AIVerse Platform`

- (Ralph) 在同一資源群組建立 `fet-mobilebot-webapp`, `fet-mobile-bot-dev`
- `fet-mobile-bot-dev`:
  - 自動建立 `Microsoft App ID` (即 `AZURE_CLIENT_ID`)，用於 service principal 辨識 Bot 身份 (MobileAgent)
  - (Ralph) 於 `Entra ID` 建立 `Microsoft App Password` (即 `AZURE_CLIENT_SECRET`)，client id 與 secret 用於通訊加密
  - (Ralph) 設定網域 `fet-mobilebot-webapp.azurewebsites.net`
- (Ralph) 設定私人端點 (Private Endpoint) 用於存取公司資源 (Foundry, Databricks)

### 2. Foundry Agent 服務設定

> 注意事項：給予 MobileAgent foundry 存取權限  
> Foundry resource: `fetdwaifndry26`  
> Foundry project: `dwfndry003`

- (Ralph) 在 Foundry 給予 MobileAgent 在專案中 Azure AI User 權限

### 3. Databricks Genie 設定

> 注意事項：給予 MobileAgent genie 存取權限  
> Databricks workspace: `fet-adb-rag-bst`

- (Will) 建立的 genie space：Finance_Dataset, Active_Dataset
- (Ralph) 在 Databricks 給予 MobileAgent 在 genie space 中 can run 權限
- 若要使用 GenieBot (不透過 foundry agent 直接與 genie 對話)，需使用 MobileAgent 的 access token，目前是由 Ralph 手動產生

## B. 上版程式調整

- 記錄錯誤與調整事項

### 1. Bot Framework Adapter 設定

- 檔案: `src/app.py`
- 事項：`BotFrameworkAdapter` 僅用於本地開發，正式部屬使用 `CloudAdapter`

#### 初始化 adapter

- CloudAdapter:
  - 需傳入一個 config 物件
  - 需包含 `APP_ID`, `APP_PASSWORD`, `APP_TYPE`, `APP_TENANTID` 四個屬性
- BotFrameworkAdapter:
  - 傳入空字串作為 app id 與 app password

```python
# 目前使用「是否設定 app id, app password 環境變數」作為判斷依據
if settings.bot["app_id"] != "" and settings.bot["app_password"] != "":
    # Production: Use CloudAdapter
    class BotConfig:
        APP_ID = settings.bot["app_id"]
        APP_PASSWORD = settings.bot["app_password"]
        APP_TYPE = settings.bot["app_type"]
        APP_TENANTID = settings.bot["app_tenantid"]

    ADAPTER = CloudAdapter(ConfigurationBotFrameworkAuthentication(BotConfig()))
    logger.info("CloudAdapter 已建立 (生產環境)")
else:
    # Local testing: Use BotFrameworkAdapter with empty credentials
    SETTINGS = BotFrameworkAdapterSettings("", "")
    ADAPTER = BotFrameworkAdapter(SETTINGS)
    logger.info("BotFrameworkAdapter 已建立 (本地開發)")
```

#### Adapter 處理訊息方式不同

- 檔案: `src/app.py`
- 事項：`BotFrameworkAdapter` 應使用 `process_activity`，`CloudAdapter` 應使用 `process` 方法
- 錯誤訊息：

```
ERROR - [on_turn_error] 未處理的錯誤: Failed to get access token with error: unauthorized_client
```

- 修改程式碼：

```python
# 根據適配器類型使用不同的處理方式
if hasattr(ADAPTER, "process"):
    # CloudAdapter - 直接使用 process 方法
    response = await ADAPTER.process(request, BOT)
    if response:
        return JSONResponse(content=response.body, status_code=response.status)
    return JSONResponse(content={}, status_code=201)
else:
    # BotFrameworkAdapter - 使用 process_activity
    response = await ADAPTER.process_activity(
        activity, auth_header, BOT.on_turn
    )
    if response:
        return JSONResponse(content=response.body, status_code=response.status)
    return JSONResponse(content={}, status_code=201)
```

### 2. 客戶端連接 Databricks Genie Token 過期

- 檔案: `src/utils/genie_tools.py`
- 事項：客戶端 (WorkspaceClient) 連接 Databricks 時，Token 過期需重新建立客戶端
- 錯誤訊息：

```
401 Unauthorized
Token is expired
```

- 修改程式碼：

```python
try:
    response = self._genies[connection_name].ask_question(question)
except Exception as e:
    # Token過期時自動重建客戶端並重試
    if "401" in str(e) or "Token is expired" in str(e):
        logger.warning(f"Token已過期,重新建立客戶端: {connection_name}")
        conn_info = self._connections[connection_name]
        token = self._credential.get_token(
            self._entra_id_audience_scope
        ).token
        self._genies[connection_name] = Genie(
            conn_info["genie_space_id"],
            client=WorkspaceClient(host=conn_info["target"], token=token),
        )
        response = self._genies[connection_name].ask_question(question)
    else:
        raise e
```
