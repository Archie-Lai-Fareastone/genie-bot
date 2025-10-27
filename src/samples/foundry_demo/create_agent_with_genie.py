"""
說明: 展示如何建立一個具有多個 Genie 函式功能的 AI 代理程式

重要元件: 
- main(): 主要執行函式，負責初始化客戶端、設定 Genie 函式並建立代理程式
- genie_configs: 儲存 Genie 空間設定的字典
- user_functions: 由 setup_genie_functions() 建立的函式清單
- toolset: 包含所有可用工具的工具集合
"""


import asyncio
import sys
import os
import json
from typing import Dict
from dotenv import load_dotenv
from databricks.sdk import WorkspaceClient
from azure.ai.agents.models import (FunctionTool, ToolSet)

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))
from samples.foundry_demo.project_operations import create_agent, get_project_client
from samples.foundry_demo.genie_connections import setup_genie_functions


load_dotenv()

async def main():
    # Environment variables
    databricks_entra_id_audience_scope = os.getenv("DATABRICKS_ENTRA_ID_AUDIENCE_SCOPE")
    path_to_genie_space_config = 'src/config/genie_space_config.json'


    # Initialize clients
    project_client, credential = get_project_client()
    print("AIProjectClient initialized")

    databricks_workspace_client = WorkspaceClient(
        host=os.getenv("DATABRICKS_HOST"),
        token=credential.get_token(databricks_entra_id_audience_scope).token,
    )
    print(f"Databricks workspace client created")


    # List project connections
    with open(path_to_genie_space_config, 'r', encoding='utf-8') as f:
        genie_space_config = json.load(f)
    
    genie_configs: Dict[str, Dict[str, str]] = {}  # {"genie_space_id": {"name": "函式名稱", "description": "函式描述"}}
    
    for connection in project_client.connections.list():
        if (connection.type == "Databricks" and 
            connection.metadata.get("azure_databricks_connection_type") == "genie"):
            
            genie_space_id = connection.metadata.get("genie_space_id")
            if genie_space_id and genie_space_id in genie_space_config:
                genie_configs[genie_space_id] = {
                    "name": genie_space_config[genie_space_id].get("name", "genie_function"),
                    "description": genie_space_config[genie_space_id].get("description", "No description")
                }


    # 建立多個 Genie 函式
    print("正在建立 Genie 函式...")
    user_functions = setup_genie_functions(genie_configs, databricks_workspace_client)
    
    if not user_functions:
        print("錯誤: 無法建立任何 Genie 函式")
        return

    print(f"成功建立 {len(user_functions)} 個 Genie 函式")

    # Add toolset
    toolset = ToolSet()
    functions = FunctionTool(functions=user_functions)
    toolset.add(functions)

    # 建立代理程式
    print("正在建立代理程式...")
    success, message, agent_id = await create_agent(
        agent_name="Archie-主要助手",
        agent_instructions="你是一個有幫助的AI助理，可以使用多個不同的 Genie 資源來回答問題。請用繁體中文回答問題。",
        toolset=toolset
    )

    print(f"success: {success} \n message: {message} \n agent_id: {agent_id}")


if __name__ == "__main__":
    asyncio.run(main())