"""
Azure AI Agent 操作範例

展示如何透過 azure.ai.project 建立和刪除代理程式。
"""

import asyncio
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../")))
from src.utils.project_operations import create_agent, delete_agent


async def main():
    """主程式範例"""
    
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