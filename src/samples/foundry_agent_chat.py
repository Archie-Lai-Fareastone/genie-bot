"""
DESCRIPTION:
    This sample demonstrates how to interact with an existing
    Azure AI Foundry agent by sending user questions and receiving responses.

USAGE:
    python sample_agent_chat.py

    Before running the sample:

    pip install azure-ai-projects azure-ai-agents azure-identity databricks-ai-bridge databricks-sdk

    Set these environment variables with your own values:
    1) AZURE_FOUNDRY_PROJECT_ENDPOINT - The endpoint of your Azure AI Foundry project.
    2) AZURE_AI_AGENT_ID - The ID of the existing agent.
    3) FOUNDRY_DATABRICKS_CONNECTION_NAME - The name of the Databricks connection.
    4) DATABRICKS_ENTRA_ID_AUDIENCE_SCOPE - The Entra ID audience scope for Databricks.
"""

import json
from databricks.sdk import WorkspaceClient
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from databricks_ai_bridge.genie import Genie, GenieResponse
from azure.ai.agents.models import FunctionTool, ToolSet
from typing import Any, Callable, Set
import os
from dotenv import load_dotenv

load_dotenv()
os.environ["DATABRICKS_SDK_UPSTREAM"] = "AzureAIFoundry"
os.environ["DATABRICKS_SDK_UPSTREAM_VERSION"] = "1.0.0"

DATABRICKS_ENTRA_ID_AUDIENCE_SCOPE = os.getenv("DATABRICKS_ENTRA_ID_AUDIENCE_SCOPE")
FOUNDRY_PROJECT_ENDPOINT = os.getenv("AZURE_FOUNDRY_PROJECT_ENDPOINT")
FOUNDRY_DATABRICKS_CONNECTION_NAME = os.getenv(
    "FOUNDRY_DATABRICKS_CONNECTION_NAME", "Active_dataset_Rag_bst"
)
AZURE_AI_AGENT_ID = os.getenv("AZURE_AI_AGENT_ID")


def genie_to_object(genie_response: GenieResponse) -> dict:
    query = genie_response.query
    result = genie_response.result
    description = genie_response.description
    return {"query": query, "result": result, "description": description}


def ask_genie(questions) -> str:
    """
    Function to ask Genie a question and get the response.
    :param questions: List of questions to ask Genie.
    :return: Response from Genie.
    """
    genie_response = genie.ask_question(questions)
    return json.dumps(genie_to_object(genie_response))


credential = DefaultAzureCredential(exclude_interactive_browser_credential=False)

project_client = AIProjectClient(FOUNDRY_PROJECT_ENDPOINT, credential)
print(f"AI Project client created for project endpoint: {FOUNDRY_PROJECT_ENDPOINT}")

connection = project_client.connections.get(FOUNDRY_DATABRICKS_CONNECTION_NAME)
print(f"Retrieved connection '{FOUNDRY_DATABRICKS_CONNECTION_NAME}' from AI project")

if connection.metadata["azure_databricks_connection_type"] == "genie":
    genie_space_id = connection.metadata["genie_space_id"]
    print(f"Connection is of type 'genie', retrieved genie space ID: {genie_space_id}")
else:
    raise ValueError(
        "Connection is not of type 'genie', please check the connection type."
    )

databricks_workspace_client = WorkspaceClient(
    host=connection.target,
    token=credential.get_token(DATABRICKS_ENTRA_ID_AUDIENCE_SCOPE).token,
)
print(f"Databricks workspace client created for host: {connection.target}")

genie = Genie(genie_space_id, client=databricks_workspace_client)
print("Genie client initialized")

toolset = ToolSet()
user_functions: Set[Callable[..., Any]] = {ask_genie}
functions = FunctionTool(functions=user_functions)
toolset.add(functions)

print("\n" + "=" * 60)
print("Chat with Agent")
print("=" * 60)
print("Type your question and press Enter. Type 'exit' to quit.\n")

with project_client:
    project_client.agents.enable_auto_function_calls(toolset)

    thread = project_client.agents.threads.create()
    print(f"Created thread, ID: {thread.id}\n")

    try:
        while True:
            user_input = input("You: ").strip()

            if user_input.lower() == "exit":
                print("Ending conversation...")
                break

            if not user_input:
                continue

            message = project_client.agents.messages.create(
                thread_id=thread.id,
                role="user",
                content=user_input,
            )
            print(f"Message sent, ID: {message.id}")

            run = project_client.agents.runs.create_and_process(
                thread_id=thread.id, agent_id=AZURE_AI_AGENT_ID
            )

            print(f"Run completed with status: {run.status}")

            messages = project_client.agents.messages.list(thread_id=thread.id)
            for message in messages:
                if message.role == "assistant":
                    print(f"\nAgent: {message.content}\n")
                    break
    finally:
        # 清理資源：刪除執行緒（選擇性）
        try:
            project_client.agents.threads.delete(thread.id)
            print(f"Thread {thread.id} deleted successfully.")
        except Exception as e:
            print(f"Could not delete thread: {e}")

print("Chat session ended.")
