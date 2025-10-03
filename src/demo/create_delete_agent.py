"""
說明: 此模組用於展示如何建立與刪除 Azure AI 代理程式，並提供簡單的操作範例。

重要元件: 
- create_agent(): 從 utils 導入，用於建立新的 Azure AI 代理程式。
- delete_agent(): 從 utils 導入，用於刪除指定的 Azure AI 代理程式。
- main(): 非同步主函式，執行建立與刪除代理程式的操作。

使用範例: 
執行此模組時，會自動建立一個名為 "測試助手" 的代理程式，並在建立後立即刪除。
"""

import asyncio
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from src.utils.project_operations import create_agent, delete_agent


async def main():
    # 建立代理程式
    print("正在建立代理程式...")
    success, message, agent_id = await create_agent(
        agent_name="測試助手",
        agent_instructions="你是一個有幫助的AI助理，請用繁體中文回答問題。"
    )

    if success:
        print(f"✅ {message}")
        print(f"代理程式 ID: {agent_id}")

        # 刪除代理程式
        print("\n正在刪除代理程式...")
        success, message = await delete_agent(agent_id)

        if success:
            print(f"✅ {message}")
        else:
            print(f"❌ {message}")
    else:
        print(f"❌ {message}")


if __name__ == "__main__":
    asyncio.run(main())