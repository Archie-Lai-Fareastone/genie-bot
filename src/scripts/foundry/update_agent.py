"""
DESCRIPTION:
    This sample demonstrates how to update an existing Microsoft Foundry Agent
    and register the chart_to_base64 tool.

USAGE:
    Set these environment variables with your own values:
    1) AZURE_FOUNDRY_PROJECT_ENDPOINT - The endpoint of your Azure AI Foundry project
    2) AZURE_FOUNDRY_AGENT_ID - The ID of the agent to update
"""

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import FunctionTool, ToolSet
from typing import Any, Callable, Set
import os
from dotenv import load_dotenv

load_dotenv()

FOUNDRY_PROJECT_ENDPOINT = os.getenv("AZURE_FOUNDRY_PROJECT_ENDPOINT")
AGENT_ID = os.getenv("AZURE_AI_AGENT_ID")

##################
# Tool Definitions for Agent Update


def ask_genie(connection_name: str, question: str) -> str:
    """
    Function to ask Genie a question and get the response.
    Only the schema is defined here; actual execution is handled in bot definition.

    :param question: Question to ask Genie.
    :param connection_name: The name of the Databricks connection. 可用選項: Active_dataset_Rag_bst (active dataset), Finance_dataset_Rag_bst (finance dataset)
    :return: Response from Genie.
    """
    pass


##################
# Update Agent


if __name__ == "__main__":
    if not AGENT_ID:
        print("❌ Error: AZURE_FOUNDRY_AGENT_ID environment variable is not set")
        print("Please set the Agent ID you want to update")
        exit(1)

    credential = DefaultAzureCredential(exclude_interactive_browser_credential=False)
    project_client = AIProjectClient(FOUNDRY_PROJECT_ENDPOINT, credential)

    print(f"AI Project client created for project endpoint: {FOUNDRY_PROJECT_ENDPOINT}")
    print(f"Updating agent with ID: {AGENT_ID}")

    # 設定工具集
    toolset = ToolSet()
    user_functions: Set[Callable[..., Any]] = {
        ask_genie,
    }
    functions = FunctionTool(functions=user_functions)
    toolset.add(functions)

    with project_client:
        # 啟用自動函式呼叫
        project_client.agents.enable_auto_function_calls(toolset)

        # 更新 agent
        agent = project_client.agents.update_agent(
            agent_id=AGENT_ID,
            instructions="""* 你是「遠傳電信大數據平台 智靈助手」
* 一律使用繁體中文問答
* 回傳格式必須包含一個或多個 card_type 以及其他對應欄位
* Genie 是取得資料的工具，如果使用者問題和 "active" 或 "finance" 資料相關，使用 ask_genie 工具取得資料，取得結果後回傳給使用者
* 使用者問題與"active" 或 "finance" 資料不相關，就不要使用 ask_genie
* 使用 ask_genie 的時候要根據使用者問題傳遞 connection_name
* 單一問題使用 ask_genie 次數不得超過 2 次
* 繪製圖表：當需要回傳圖表時,請直接使用 card_type="chart" 並提供 chart_type, labels, values 欄位。確保labels, values長度相同。
            """,
            toolset=toolset,
        )

        print(f"\n✓ Agent '{agent.name}' updated successfully")
        print(f"  Model: {agent.model}")
        print(f"  Agent ID: {agent.id}")
        print(f"  Tools: {len(user_functions)} functions registered")
