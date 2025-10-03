import os
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from dotenv import load_dotenv

load_dotenv()

project_client = AIProjectClient(
    credential=DefaultAzureCredential(),
    endpoint=os.environ["AZURE_AI_AGENT_ENDPOINT"],
)

print("List all connections:")
for connection in project_client.connections.list():
    print("="*40)
    print(connection)
