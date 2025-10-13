import json
import os
import logging
from typing import Dict, List, Optional
import asyncio
from dotenv import load_dotenv
from botbuilder.core import ActivityHandler, TurnContext, MessageFactory
from botbuilder.schema import ChannelAccount
from azure.identity.aio import AzureCliCredential
from semantic_kernel.agents import AzureAIAgent, AzureAIAgentThread


# 載入環境變數
load_dotenv()


# 設定日誌記錄
handler = logging.FileHandler("bot_conversations.log")
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        handler,
        logging.StreamHandler()  # 輸出到控制台
    ]
)

# 針對 Azure SDK 相關模組降低記錄層級
logging.getLogger('azure').setLevel(logging.WARNING)
logging.getLogger('azure.core').setLevel(logging.WARNING) 
logging.getLogger('semantic_kernel').setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


class MyBot(ActivityHandler):
    def __init__(self):
        self.thread_dict: Dict[str, AzureAIAgentThread] = {}
        self.agent: AzureAIAgent = None


    async def init_agent(self):
        credential = AzureCliCredential()
        client = AzureAIAgent.create_client(credential=credential)
        agent_id = os.getenv("AZURE_AI_AGENT_ID")
        agent_definition = await client.agents.get_agent(agent_id)

        logger.info(f"代理程式名稱: {agent_definition.name}")
        self.agent = AzureAIAgent(client=client, definition=agent_definition)
        logger.info("AzureAIAgent 已初始化")


    async def ask_agent(self, user_input: str, user_id: str):
        thread = self.thread_dict.get(user_id, None)
        response = await self.agent.get_response(messages=user_input, thread=thread)
        logger.info(f"代理程式 {self.agent.definition.name}: {response}")
        
        self.thread_dict[user_id] = response.thread
        return f'{response}'


    def reset_thread(self, user_id):
        if user_id in self.thread_dict:
            self.thread_dict[user_id] = None
        logger.info("對話已重置")


    async def on_message_activity(self, turn_context: TurnContext):
        question = turn_context.activity.text.strip()
        user_id = turn_context.activity.from_property.id

        # 檢查 agent 是否已初始化
        if self.agent is None:
            await self.init_agent()
        
        # 檢查是否為重置命令
        if question.lower() in ['重新開始', 'reset', '新對話', 'new']:
            self.reset_thread(user_id)
            await turn_context.send_activity("對話已重新開始！請問您有什麼問題？")
            return

        try:
            output_message = await self.ask_agent(user_input=question, user_id=user_id)
            
            if isinstance(output_message, str):
                # 純文字回覆
                await turn_context.send_activity(output_message)

            else:
                logger.warning(f"未知的回覆格式: {type(output_message)}")
                await turn_context.send_activity("抱歉，我無法處理您的請求。")

        except Exception as e:
            logger.error(f"處理訊息時發生錯誤: {str(e)}")
            await turn_context.send_activity(
                f"處理您的請求時發生錯誤。{e}"
            )


    async def on_members_added_activity(
        self,
        members_added: List[ChannelAccount],
        turn_context: TurnContext
    ):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity("歡迎使用 Databricks Genie Bot！")