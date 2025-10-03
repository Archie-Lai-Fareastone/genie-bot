"""
此腳本展示了如何使用 Azure AI Agent 與 Semantic Kernel。

功能：
1. 使用 Azure CLI 憑證進行身份驗證。
2. 在 Azure AI Agent 服務上建立 AI Agent。
3. 允許使用者透過終端機進行互動式輸入。
4. 在程式結束時清理資源（Thread 和 Agent）。

使用方式：
- 在終端機中執行此腳本。
- 輸入文字與 AI Agent 互動。
- 輸入 'quit' 以退出並清理資源。

必要條件：
- 已安裝並登入 Azure CLI（執行 `az login`）。
- 已安裝必要的 Python 套件（請參考 requirements.txt）。

"""

import asyncio
from azure.identity.aio import AzureCliCredential
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentSettings, AzureAIAgentThread


async def main() -> None:
    async with (
        AzureCliCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        # 1. Create an agent on the Azure AI agent service
        agent_definition = await client.agents.create_agent(
            model=AzureAIAgentSettings().model_deployment_name,
            name="Archie-test-agent",
            instructions="Answer the user's questions.",
        )

        # 2. Create a Semantic Kernel agent for the Azure AI agent
        agent = AzureAIAgent(
            client=client,
            definition=agent_definition,
        )

        # 3. Create a thread for the agent
        thread: AzureAIAgentThread = None

        try:
            print("歡迎使用 AI 助手！輸入 'quit' 來結束對話。")
            print("-" * 50)
            
            while True:
                # 4. Get user input from terminal
                user_input = input("請輸入一些文字或 'quit' 來結束。: ").strip()
                
                if user_input.lower() == 'quit':
                    print("再見！正在清理資源...")
                    break
                
                print(f"# 使用者: {user_input}")

                # 5. Invoke the agent with the specified message for response
                response = await agent.get_response(messages=user_input, thread=thread)
                print(f"# {response.name}: {response}")
                thread = response.thread
        finally:
            # 6. Cleanup: Delete the thread and agent
            if thread:
                await thread.delete()
                print("Thread 已刪除")
            await client.agents.delete_agent(agent.id)
            print("Agent 已刪除")


if __name__ == "__main__":
    asyncio.run(main())