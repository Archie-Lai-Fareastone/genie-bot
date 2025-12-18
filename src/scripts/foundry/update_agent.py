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

from utils.chart_tools import chart_to_base64

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
    :param connection_name: The name of the Databricks connection.
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
    user_functions: Set[Callable[..., Any]] = {ask_genie, chart_to_base64}
    functions = FunctionTool(functions=user_functions)
    toolset.add(functions)

    with project_client:
        # 啟用自動函式呼叫
        project_client.agents.enable_auto_function_calls(toolset)

        # 更新 agent
        agent = project_client.agents.update_agent(
            agent_id=AGENT_ID,
            instructions=(
                "You're a helpful assistant. "
                "Use the ask_genie tool to answer questions by querying Databricks Genie. "
                "Always specify the correct connection_name based on the user's question. "
                "When you receive data that would benefit from visualization, use the chart_to_base64 tool "
                "to generate charts. Choose the appropriate chart_type based on the data structure."
            ),
            toolset=toolset,
        )

        print(f"\n✓ Agent '{agent.name}' updated successfully")
        print(f"  Model: {agent.model}")
        print(f"  Agent ID: {agent.id}")
        print(f"  Tools: {len(user_functions)} functions registered")
        print(f"    - ask_genie")
        print(f"    - chart_to_base64")
