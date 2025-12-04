"""
說明: 列出所有專案連線的腳本。

重要元件:
- AIProjectClient: 用於與 Azure AI 專案進行互動的客戶端。
- DefaultAzureCredential: 用於驗證 Azure 的預設憑證。
"""

import os
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

load_dotenv()

project_client = AIProjectClient(
    credential=DefaultAzureCredential(),
    endpoint=os.environ["AZURE_FOUNDRY_PROJECT_ENDPOINT"],
)

print("List all connections:")
for connection in project_client.connections.list():
    print("=" * 40)
    print(connection)
