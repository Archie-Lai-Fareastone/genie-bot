"""
DESCRIPTION:
    This sample demonstrates how to create a Microsoft Foundry Agent that can interact with Databricks Genie using a custom tool.

USAGE:
    Set these environment variables with your own values:
    1) FOUNDRY_PROJECT_ENDPOINT - The endpoint of your Azure AI Foundry project, as found in the "Overview" tab
       in your Azure AI Foundry project.
"""

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import FunctionTool, ToolSet
from typing import Any, Callable, Set
import os
from dotenv import load_dotenv

load_dotenv()

FOUNDRY_PROJECT_ENDPOINT = os.getenv("AZURE_FOUNDRY_PROJECT_ENDPOINT")
AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME = os.getenv("AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME")
AZURE_AI_AGENT_NAME = os.getenv("AZURE_AI_AGENT_NAME")

##################
# Tool Definition for Agent Creation


def ask_genie(connection_name: str, question: str) -> str:
    """
    Function to ask Genie a question and get the response.
    Only the schema is defined here; actual execution is handled in bot definition.

    :param question: Question to ask Genie.
    :param connection_name: The name of the Databricks connection. 可用選項: Active_dataset_Rag_bst (active dataset), Finance_dataset_Rag_bst (finance dataset)
    :return: Response from Genie.
    """
    # 這個函式只是用來定義工具的 schema
    # 實際執行時會在 bot.py 中的 Bot.ask_genie 方法中處理
    pass


##################
# Create Agent


if __name__ == "__main__":
    credential = DefaultAzureCredential(exclude_interactive_browser_credential=False)

    project_client = AIProjectClient(FOUNDRY_PROJECT_ENDPOINT, credential)
    print(f"AI Project client created for project endpoint: {FOUNDRY_PROJECT_ENDPOINT}")

    # 設定工具集
    toolset = ToolSet()
    user_functions: Set[Callable[..., Any]] = {ask_genie}
    functions = FunctionTool(functions=user_functions)
    toolset.add(functions)

    with project_client:
        # 建立 agent
        project_client.agents.enable_auto_function_calls(toolset)

        agent = project_client.agents.create_agent(
            model=AZURE_AI_AGENT_MODEL_DEPLOYMENT_NAME,
            name=AZURE_AI_AGENT_NAME,
            instructions="""* 一律使用繁體中文問答
* 回傳格式必須包含一個或多個 card_type 以及其他對應欄位
* 如果使用者問題和 "active" 或 "finance" 資料相關，使用 ask_genie 工具取得資料，取得結果後回傳給使用者
* 使用 ask_genie 的時候要根據使用者問題傳遞 connection_name
* 單一問題使用 ask_genie 次數不得超過 2 次
            """,
            toolset=toolset,
        )

        print(f"✓ Agent '{agent.name}' created successfully")
        print(f"  Model: {agent.model}")
        print(f"  Agent ID: {agent.id}")
        print(
            f"\nPlease save this Agent ID to your environment variables as AZURE_FOUNDRY_AGENT_ID"
        )
