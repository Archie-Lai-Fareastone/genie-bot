@echo off
REM Azure App Service 部署腳本
REM 使用方式: deploy.bat [部署|設定|日誌|重啟]

echo ====================================
echo Azure App Service 部署工具
echo ====================================
echo.

REM ===== 設定變數 (請修改為您的實際名稱) =====
set APP_NAME=genie-bot-app
set RESOURCE_GROUP=genie-bot-rg

REM ===== 檢查參數 =====
if "%1"=="" (
    echo 請選擇操作:
    echo   1. 部署 - 部署程式碼到 Azure
    echo   2. 設定 - 顯示環境變數設定說明
    echo   3. 日誌 - 查看即時日誌
    echo   4. 重啟 - 重新啟動應用程式
    echo   5. 狀態 - 查看應用程式狀態
    echo.
    set /p choice="請輸入選項 (1-5): "
) else (
    set choice=%1
)

REM ===== 執行操作 =====
if "%choice%"=="1" goto DEPLOY
if "%choice%"=="2" goto CONFIG
if "%choice%"=="3" goto LOGS
if "%choice%"=="4" goto RESTART
if "%choice%"=="5" goto STATUS
if "%choice%"=="部署" goto DEPLOY
if "%choice%"=="設定" goto CONFIG
if "%choice%"=="日誌" goto LOGS
if "%choice%"=="重啟" goto RESTART
if "%choice%"=="狀態" goto STATUS
echo 無效的選項
goto END

:DEPLOY
echo.
echo 正在部署程式碼到 Azure...
echo 應用程式: %APP_NAME%
echo 資源群組: %RESOURCE_GROUP%
echo.
call az webapp up ^
    --name %APP_NAME% ^
    --resource-group %RESOURCE_GROUP% ^
    --runtime "PYTHON:3.12"
if errorlevel 1 goto ERROR

echo.
echo ✓ 部署完成!
echo 應用程式網址: https://%APP_NAME%.azurewebsites.net
echo Bot 端點: https://%APP_NAME%.azurewebsites.net/api/messages
goto END

:CONFIG
echo.
echo 設定環境變數...
echo 請在 Azure Portal 手動設定以下環境變數:
echo   - DATABRICKS_HOST
echo   - DATABRICKS_TOKEN
echo   - DATABRICKS_ENTRA_ID_AUDIENCE_SCOPE
echo   - MAX_CARD_ROWS=30
echo   - MAX_CARD_COLUMNS=7
echo   - PORT=8000
echo   - WEBSITES_PORT=8000
echo   - SCM_DO_BUILD_DURING_DEPLOYMENT=true
echo.
echo 或執行以下命令 (需先設定變數值):
echo az webapp config appsettings set --name %APP_NAME% --resource-group %RESOURCE_GROUP% --settings DATABRICKS_HOST="your-value"
echo.
if "%choice%"=="4" (
    echo ✓ 完整部署完成!
    echo 請記得在 Azure Portal 設定環境變數
)
goto END

:LOGS
echo.
echo 取得即時日誌...
echo 按 Ctrl+C 可停止
echo.
call az webapp log tail --name %APP_NAME% --resource-group %RESOURCE_GROUP%
goto END

:RESTART
echo.
echo 重新啟動應用程式...
call az webapp restart --name %APP_NAME% --resource-group %RESOURCE_GROUP%
if errorlevel 1 goto ERROR
echo ✓ 應用程式已重新啟動
goto END

:STATUS
echo.
echo 查看應用程式狀態...
echo.
echo === 基本資訊 ===
call az webapp show --name %APP_NAME% --resource-group %RESOURCE_GROUP% --query "{name:name, state:state, defaultHostName:defaultHostName, httpsOnly:httpsOnly}" --output table
echo.
echo === 應用程式設定 ===
call az webapp config appsettings list --name %APP_NAME% --resource-group %RESOURCE_GROUP% --query "[].{name:name, value:value}" --output table
goto END

:ERROR
echo.
echo ✗ 部署過程中發生錯誤!
echo 請檢查錯誤訊息並修正後重試
exit /b 1

:END
echo.
echo ====================================
