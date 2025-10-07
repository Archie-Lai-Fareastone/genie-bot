# Databricks Genie Bot

此機器人已使用 [Bot Framework](https://dev.botframework.com) 建立，展示如何建立一個能與 Databricks Genie API 互動的聊天機器人。機器人可以接受用戶的自然語言查詢，並透過 Databricks Genie 返回智慧回應和查詢結果。

## 設定

1. 複製 `.env.example` 檔案並重新命名為 `.env`
2. 在 `.env` 檔案中填入以下資訊：
   - `DATABRICKS_HOST`: 您的 Databricks 工作區 URL
   - `DATABRICKS_TOKEN`: 您的 Databricks 存取權杖
   - `DATABRICKS_SPACE_ID`: 您的 Genie 空間 ID

### 取得 Databricks 設定

1. **Databricks Host**: 您的 Databricks 工作區 URL（例如：`https://your-workspace.cloud.databricks.com`）
2. **Databricks Token**: 
   - 登入您的 Databricks 工作區
   - 前往 Settings > User Settings > Access Tokens
   - 產生新的存取權杖
3. **Genie Space ID**:
   - 在 Databricks 中前往您的 Genie 空間
   - 從 URL 中複製空間 ID

## 執行範例
- 執行 `pip install -r requirements.txt` 以安裝所有相依套件
- 執行 `python app.py`

## 使用 Bot Framework Emulator 測試機器人

[Bot Framework Emulator](https://github.com/microsoft/botframework-emulator) 是一個桌面應用程式，允許機器人開發者在 localhost 上測試和除錯他們的機器人。

- 從[這裡](https://github.com/Microsoft/BotFramework-Emulator/releases)安裝 Bot Framework Emulator 版本 4.3.0 或更高版本

### 使用 Bot Framework Emulator 連接到機器人

- 啟動 Bot Framework Emulator
- 輸入機器人 URL：`http://localhost:3978/api/messages`

## 功能

- **自然語言查詢**: 使用自然語言向 Databricks Genie 提問
- **智慧回應**: 獲得 AI 驅動的資料分析和見解
- **查詢結果**: 以表格格式顯示結構化查詢結果
- **對話持續性**: 維護與每個用戶的對話上下文

## 故障排除

如果遇到連接問題，請檢查：
1. 您的 Databricks 權杖是否有效且具有適當權限
2. Genie 空間 ID 是否正確
3. 網路連接是否正常

## 進一步閱讀

- [Bot Framework 文件](https://docs.botframework.com)
- [Databricks Genie API 文件](https://docs.databricks.com/en/genie/index.html)
- [Azure Bot Service 簡介](https://docs.microsoft.com/azure/bot-service/bot-service-overview-introduction?view=azure-bot-service-4.0)