# Azure App Service 快速部署指南

> **前提**: 管理員已建立好 Resource Group、App Service Plan 和 Web App

## 📁 需要的檔案

✅ 以下檔案已準備完成：

1. **`deploy.bat`** ⭐ - 部署腳本
2. **`startup.txt`** - 啟動命令
3. **`runtime.txt`** - Python 版本
4. **`requirements.txt`** - 相依套件
5. **`.deployment`** - 建構設定

## 🚀 三步驟快速部署

### 步驟 1: 修改設定
編輯 `deploy.bat`，修改為實際名稱：
```batch
set APP_NAME=genie-bot-app
set RESOURCE_GROUP=genie-bot-rg
```

### 步驟 2: 登入 Azure
```cmd
az login
```

### 步驟 3: 部署程式碼
```cmd
deploy.bat 1
```

✅ 完成！

## 📋 常用操作

### 使用互動式選單
```cmd
deploy.bat
```
選擇選項：
- `1` - 部署程式碼
- `2` - 環境變數設定說明
- `3` - 查看即時日誌
- `4` - 重新啟動應用程式
- `5` - 查看應用程式狀態

### 直接執行
```cmd
deploy.bat 1    # 部署程式碼
deploy.bat 3    # 查看日誌 (Ctrl+C 停止)
deploy.bat 4    # 重啟應用程式
deploy.bat 5    # 查看狀態
```

## 🔐 部署後設定

在 Azure Portal 設定環境變數：

**位置**: Azure Portal → App Service → 設定 → 環境變數

### 必要變數
- `DATABRICKS_HOST`
- `DATABRICKS_TOKEN`
- `DATABRICKS_ENTRA_ID_AUDIENCE_SCOPE`

### 建議變數
- `MAX_CARD_ROWS=30`
- `MAX_CARD_COLUMNS=7`
- `PORT=8000`
- `WEBSITES_PORT=8000`

## 🌐 應用程式網址

部署完成後：
- **應用程式**: `https://genie-bot-app.azurewebsites.net`
- **Bot 端點**: `https://genie-bot-app.azurewebsites.net/api/messages`

## ❗ 疑難排解

### 部署失敗
```cmd
az account show    # 檢查登入狀態
az login          # 重新登入
```

### 應用程式無法啟動
```cmd
deploy.bat 3      # 查看日誌
```

### 環境變數未生效
```cmd
deploy.bat 5      # 查看設定
deploy.bat 4      # 重啟應用程式
```

### 權限不足
- 確認帳號有 Web App 的 Contributor 權限
- 聯繫管理員授予權限

## 📚 進階命令 (Azure CLI)

```cmd
# 查看日誌
az webapp log tail --name genie-bot-app --resource-group genie-bot-rg

# 重啟應用程式
az webapp restart --name genie-bot-app --resource-group genie-bot-rg

# 查看設定
az webapp config appsettings list --name genie-bot-app --resource-group genie-bot-rg

# 查看應用程式資訊
az webapp show --name genie-bot-app --resource-group genie-bot-rg
```

---

**快速開始**: `deploy.bat 1` 即可部署！
