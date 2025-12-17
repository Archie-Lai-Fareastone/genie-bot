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

##################
# Tool Definition for Agent Creation


def ask_genie(connection_name: str, question: str) -> str:
    """
    向指定的 Genie 提問（此函式僅用於工具定義，實際執行在 bot.py）

    Args:
        connection_name: Genie 連線名稱
        question: 要詢問的問題

    Returns:
        JSON 格式的回應，包含 query, result, description
    """
    # 這個函式只是用來定義工具的 schema
    # 實際執行時會在 bot.py 中的 MyBot.ask_genie 方法中處理
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
            model="gpt-4o-mini",
            name="Archie_agent-2",
            instructions="You're a helpful assistant. Use the ask_genie tool to answer questions by querying Databricks Genie. Always specify the correct connection_name based on the user's question.",
            toolset=toolset,
        )

        print(f"✓ Agent '{agent.name}' created successfully")
        print(f"  Model: {agent.model}")
        print(f"  Agent ID: {agent.id}")
        print(
            f"\nPlease save this Agent ID to your environment variables as AZURE_FOUNDRY_AGENT_ID"
        )
