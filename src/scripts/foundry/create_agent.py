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
    Function to ask Genie a question and get the response.
    Only the schema is defined here; actual execution is handled in bot definition.

    :param question: Question to ask Genie.
    :param connection_name: The name of the Databricks connection. 可用選項: Active_dataset_Rag_bst (active dataset), Finance_dataset_Rag_bst (finance dataset)
    :return: Response from Genie.
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
            instructions="""**IMPORTANT: Always use adaptive_card tool and return only the json content without any additional explanation.  
* The correct syntax should start with {
    "type": "AdaptiveCard",
    "version": "1.5",
    "body": [...**
* For data querying tasks, Use the ask_genie tool to get answers by querying Databricks Genie and then present the results using adaptive_card. When using ask_genie, always specify the correct connection_name based on the user's question.
* 一律使用繁體中文問答 
            """,
            toolset=toolset,
        )

        print(f"✓ Agent '{agent.name}' created successfully")
        print(f"  Model: {agent.model}")
        print(f"  Agent ID: {agent.id}")
        print(
            f"\nPlease save this Agent ID to your environment variables as AZURE_FOUNDRY_AGENT_ID"
        )
