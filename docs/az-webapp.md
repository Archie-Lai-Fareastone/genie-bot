### 查看 webapp 設定

```cmd
az webapp config show ^
    --resource-group fet-rag-bst-rg ^
    --name fet-mobilebot-webapp
```

### 部署 webapp

- 打包成 `deploy.zip` 檔案

```cmd
tar -a -c -f deploy.zip src requirements.txt
```

```cmd
az webapp deploy ^
    --name fet-mobilebot-webapp ^
    --resource-group fet-rag-bst-rg ^
    --src-path deploy.zip ^
    --type zip
```

### 啟動命令

- 寫在 web app portal 設定 -> 堆疊設定 -> 啟動命令

```sh
python3 -m uvicorn src.app:app --host 0.0.0.0 --port 8000 --workers 2 --log-level info
```
