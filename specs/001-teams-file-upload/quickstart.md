# Quickstart: Teams File Upload

## Prerequisites

1. **Azure AD App Registration**:

   - Ensure the Service Principal has **Application** permissions for Microsoft Graph:
     - `Files.Read.All`
   - Grant **Admin Consent** in the Azure Portal.

2. **Environment Variables**:
   Update your `.env` file with the following variables (existing `AZURE_CLIENT_ID`, `AZURE_CLIENT_SECRET`, and `AZURE_TENANT_ID` are reused for Graph API):

   ```env
   AZURE_CLIENT_ID=<your-service-principal-client-id>
   AZURE_CLIENT_SECRET=<your-service-principal-secret>
   AZURE_TENANT_ID=<your-azure-tenant-id>
   ```

## Azure AD 權限設定步驟

### 1. 前往 Azure Portal

1. 登入 [Azure Portal](https://portal.azure.com)
2. 導航至 **Azure Active Directory** > **App registrations**
3. 選擇你的 Bot 應用程式註冊

### 2. 設定 API 權限

1. 點擊左側選單的 **API permissions**
2. 點擊 **Add a permission**
3. 選擇 **Microsoft Graph**
4. 選擇 **Application permissions**
5. 搜尋並勾選以下權限：
   - `Files.Read.All` - 讀取所有檔案
6. 點擊 **Add permissions**

### 3. 授予管理員同意

1. 在 API permissions 頁面，點擊 **Grant admin consent for [Your Organization]**
2. 確認授予同意
3. 確認權限狀態顯示綠色勾號 ✓

## 部署步驟

### 1. 安裝相依套件

確保已安裝所有必要的 Python 套件：

```bash
pip install -r requirements.txt
```

主要新增的相依套件：

- `requests` - 用於 HTTP 請求和檔案下載
- `botbuilder-schema` - Teams schema 支援（已存在）

### 2. 本地測試

使用 Bot Framework Emulator 或直接部署到 Azure：

```bash
python src/app.py
```

### 3. 部署到 Azure Web App

```bash
az webapp up --name <your-webapp-name> --resource-group <your-resource-group>
```

## 功能整合指南

### 在 Bot 中觸發檔案上傳

在你的 bot 對話流程中，可以透過以下方式請求使用者上傳檔案：

```python
# 範例：在 FoundryBot 的訊息處理中
if "上傳檔案" in question:
    await self.file_handler.send_file_consent_card(
        turn_context,
        filename="document.pdf",
        description="請上傳您的文件"
    )
    return
```

### 設定預期檔案數量

如果需要使用者上傳多個檔案：

```python
conversation_id = turn_context.activity.conversation.id
self.file_handler.create_upload_state(
    conversation_id,
    expected_files=3  # 預期 3 個檔案
)

# 發送多個檔案同意卡片
for i in range(3):
    await self.file_handler.send_file_consent_card(
        turn_context,
        filename=f"document_{i+1}.pdf",
        description=f"請上傳第 {i+1} 個文件"
    )
```

### 處理上傳的檔案

檔案上傳後，`on_teams_file_consent_accept` 會自動被調用。你可以在此方法中：

1. 下載檔案內容
2. 儲存到本地或雲端儲存
3. 進行檔案處理（例如：傳送給 AI Agent 分析）

```python
# 在 on_teams_file_consent_accept 中
uploaded_file = await self.file_handler.handle_file_consent_accept(
    turn_context,
    file_consent_response
)

# 下載檔案內容
content = await self.file_handler.download_file(uploaded_file.download_url)

# 處理檔案（例如：儲存、分析等）
# ... your custom logic ...
```

## Testing

### 1. 部署到 Azure

確保你的 Bot 已部署並在 Teams 中正確註冊。

### 2. 在 Teams 中開始對話

1. 在 Teams 中開啟與你的 Bot 的聊天
2. 發送訊息觸發檔案上傳流程（根據你的實作邏輯）

### 3. 上傳檔案

1. 點擊檔案同意卡片的「接受」按鈕
2. 選擇要上傳的檔案
3. 確認上傳

### 4. 驗證結果

1. 檢查 Bot 是否發送了檔案上傳確認 Adaptive Card
2. 確認卡片顯示正確的檔案資訊（名稱、大小、類型）
3. 檢查應用程式日誌確認檔案已成功下載

### 5. 檢查日誌

查看應用程式日誌以確認：

- Graph API 認證成功
- 檔案下載成功
- 沒有權限錯誤

```bash
# Azure 中查看日誌
az webapp log tail --name <your-webapp-name> --resource-group <your-resource-group>
```

## 常見問題排解

### 問題 1: 403 Forbidden 錯誤

**原因**: Service Principal 沒有足夠的權限

**解決方案**:

1. 確認已在 Azure AD 中設定 `Files.Read.All` 應用程式權限
2. 確認已授予管理員同意
3. 等待幾分鐘讓權限生效

### 問題 2: 檔案下載失敗

**原因**: 下載 URL 可能已過期或需要特殊處理

**解決方案**:

1. 確認在收到 `fileConsentAccept` 事件後立即下載
2. 檢查網路連線
3. 查看詳細的錯誤日誌

### 問題 3: 令牌快取問題

**原因**: 快取的令牌可能已過期

**解決方案**:

1. GraphService 會自動處理令牌刷新
2. 如有問題，重啟應用程式清除快取
3. 檢查 `AZURE_CLIENT_SECRET` 是否正確

### 問題 4: 無法看到檔案上傳確認卡片

**原因**: Adaptive Card 格式或發送問題

**解決方案**:

1. 檢查應用程式日誌中的錯誤訊息
2. 確認 `create_file_upload_confirmation_card` 函式正常運作
3. 測試 Adaptive Card JSON 格式是否正確

## 安全性建議

1. **永不在日誌中記錄完整的存取令牌**
2. **使用 HTTPS** 進行所有通訊
3. **定期輪換 Service Principal 密鑰**
4. **實作檔案大小限制**（已在程式碼中設定為 100MB）
5. **驗證檔案類型**，避免惡意檔案上傳
6. **使用病毒掃描服務**處理上傳的檔案

## 效能優化

1. **令牌快取**: GraphService 已實作令牌快取，避免重複認證
2. **非同步處理**: 使用 `async/await` 處理檔案下載
3. **超時設定**: 下載請求設定 30 秒超時
4. **檔案大小限制**: 設定最大檔案大小為 100MB

## 下一步

1. **整合檔案處理邏輯**: 將上傳的檔案傳送給 AI Agent 進行分析
2. **儲存管理**: 實作檔案儲存到 Azure Blob Storage
3. **使用者回饋**: 加強錯誤處理和使用者提示
4. **單元測試**: 為 `FileHandler` 和 `GraphService` 編寫測試
