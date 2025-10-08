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

from src.utils.adaptive_card import (
    create_table_adaptive_card,
    create_text_adaptive_card,
    create_error_adaptive_card,
    create_adaptive_card_attachment
)

from src.demo.bot_demo.config import DefaultConfig

# 載入環境變數
load_dotenv()

CONFIG = DefaultConfig()

# 設定日誌記錄
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()  # 輸出到控制台
    ]
)
logger = logging.getLogger(__name__)


class MyBot(ActivityHandler):
    def __init__(self):
        self.conversation_ids: Dict[str, str] = {}
        self.agent: AzureAIAgent = None
        self.thread: AzureAIAgentThread = None

    async def init_agent(self):
        credential = AzureCliCredential()
        client = AzureAIAgent.create_client(credential=credential)
        agent_id = os.getenv("AZURE_AI_AGENT_ID")
        agent_definition = await client.agents.get_agent(agent_id)

        logger.info(f"代理程式名稱: {agent_definition.name}")
        self.agent = AzureAIAgent(client=client, definition=agent_definition)
        logger.info("AzureAIAgent 已初始化")


    async def ask_agent(self, user_input: str):
        response = await self.agent.get_response(messages=user_input, thread=self.thread)
        logger.info(f"代理程式回覆: {response}")
        return f'{response}'

    def reset_thread(self, user_id):
        if user_id in self.conversation_ids:
            del self.conversation_ids[user_id]
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
        
        # 繼續現有對話
        conversation_id = self.conversation_ids.get(user_id, None)
        logger.info(f"使用者 {user_id} 的現有對話 ID: {conversation_id}")

        try:
            new_conversation_id = conversation_id 

            self.conversation_ids[user_id] = new_conversation_id
            logger.info(f"更新使用者 {user_id} 的對話 ID: {new_conversation_id}")

            output_message = await self.ask_agent(user_input=question,)
            
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

    def get_text_card(self, message: str):
        text_card = create_text_adaptive_card(message)
        adaptive_card_attachment = create_adaptive_card_attachment(text_card)
        message_with_card = MessageFactory.attachment(adaptive_card_attachment)

        return message_with_card
