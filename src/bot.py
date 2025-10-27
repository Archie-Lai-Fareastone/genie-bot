from typing import Dict, List
from botbuilder.core import ActivityHandler, TurnContext, MessageFactory
from botbuilder.schema import ChannelAccount

from src.connectors.genie_connector import GenieConnector
from src.utils.adaptive_card import create_menu_card
from src.utils.logger_config import get_logger
from src.config.genie_space_config import get_genie_config

# 取得 logger 實例
logger = get_logger(__name__)


class MyBot(ActivityHandler):
    """
    Teams Bot 主類別
    
    使用 GenieConnector 處理與 Databricks Genie Space 的互動
    """
    
    def __init__(self):
        """初始化 MyBot，建立 GenieConnector 實例"""
        self.conversation_ids: Dict[str, str] = {} # 儲存使用者對話 ID
        self.connector = GenieConnector()
        logger.info("MyBot 已初始化，GenieConnector 已建立")


    async def on_turn(self, turn_context: TurnContext):
        logger.info(f"Bot on_turn 被呼叫，活動類型: {turn_context.activity.type}")
        await super().on_turn(turn_context)


    async def on_message_activity(self, turn_context: TurnContext):
        question = turn_context.activity.text.strip() if turn_context.activity.text else ""
        user_id = turn_context.activity.from_property.id
        
        logger.info(f"收到使用者 {user_id} 的訊息: {question}")
        
        # 檢查是否為重置命令
        if question.lower() in ['重新開始', 'reset', '新對話', 'new']:
            if user_id in self.conversation_ids:
                del self.conversation_ids[user_id]
            message_activity = MessageFactory.attachment(create_menu_card())
            await turn_context.send_activity(message_activity)
        
        conversation_id = self.conversation_ids.get(user_id, None)
        logger.info(f"使用者 {user_id} 的現有對話 ID: {conversation_id}")

        # 檢查是否為使用者提交資料
        if turn_context.activity.value:
            submitted_data = turn_context.activity.value
            # 檢查是否有選擇 Genie Space
            if "genie_space_id" in submitted_data:
                space_id = submitted_data["genie_space_id"]
                self.connector.set_space_id(space_id)
                logger.info(f"使用者選擇的 Genie Space ID: {space_id}")
                
                # 取得 Genie Space 名稱
                genie_config = get_genie_config(space_id)
                space_name = genie_config['name'] if genie_config else "未知"
                
                await turn_context.send_activity(f"已選擇：{space_name}")
                return

        # 詢問 Connector
        try:
            logger.info(f"呼叫 Connector.ask_question - 問題: {question}, Space ID: {self.connector.get_space_id()}")
            response_card, new_conversation_id = await self.connector.ask_question(
                question, conversation_id
            )
            
            self.conversation_ids[user_id] = new_conversation_id
            await turn_context.send_activity(MessageFactory.attachment(response_card))
            
        except Exception as e:
            logger.error(f"處理訊息時發生錯誤: {str(e)}", exc_info=True)
            await turn_context.send_activity(
                f"處理您的請求時發生錯誤: {str(e)}"
            )

    async def on_members_added_activity(
        self,
        members_added: List[ChannelAccount],
        turn_context: TurnContext
    ):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity("歡迎使用 Databricks Genie Bot！")

                # 主選單
                message_activity = MessageFactory.attachment(create_menu_card())
                logger.info("發送主選單回應")
                await turn_context.send_activity(message_activity)
            
