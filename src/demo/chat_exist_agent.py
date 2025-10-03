"""
說明: 此模組用於與已存在的 Azure AI 代理程式進行互動，允許使用者輸入文字並獲取代理程式的回應。

重要元件: 
- chat_exist_agent(agent_id: str): 主函式，負責與 Azure AI 代理程式進行互動。
- AzureCliCredential: 用於 Azure 身份驗證的非同步憑證物件。
- AzureAIAgent: 表示 Azure AI 代理程式的物件。
- AzureAIAgentThread: 用於管理代理程式對話執行緒的物件。

使用範例: 
執行此模組時，使用者需提供 Agent ID，然後可以輸入文字與代理程式互動，直到輸入 'quit' 結束對話。
"""

from azure.identity.aio import AzureCliCredential
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentThread
import asyncio


async def chat_exist_agent(agent_id: str) -> None:
    async with (
        AzureCliCredential() as creds,
        AzureAIAgent.create_client(credential=creds) as client,
    ):
        try:
            agent_definition = await client.agents.get_agent(agent_id)
        except Exception as e:
            print(f"❌ 無法取得代理程式，請確認 Agent ID 是否正確。錯誤訊息: {e}")
            return

        print(f"\n🤖 開始對話 - {agent_definition.name}")

        # 建立代理程式物件
        agent = AzureAIAgent(client=client, definition=agent_definition)
        thread: AzureAIAgentThread = None

        try:
            while True:
                user_input = input("請輸入一些文字或 'quit' 來結束。: ").strip()

                if user_input.lower() == 'quit':
                    print("再見！正在清理資源...")
                    break
                
                print(f"# 使用者: {user_input}")

                response = await agent.get_response(messages=user_input, thread=thread)
                print(f"# {response.name}: {response}")
                thread = response.thread
        except Exception as e:
            print(f"❌ 對話過程中發生錯誤: {e}")
        finally:
            if thread:
                await thread.delete()
                print("Thread 已刪除")


if __name__ == "__main__":
    agent_id = input("請輸入 Agent ID: ").strip()
    asyncio.run(chat_exist_agent(agent_id))