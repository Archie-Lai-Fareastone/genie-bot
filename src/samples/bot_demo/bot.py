import json
import logging
from typing import Dict, List, Optional
import asyncio
from dotenv import load_dotenv
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.dashboards import GenieAPI
from botbuilder.core import ActivityHandler, TurnContext, MessageFactory
from botbuilder.schema import ChannelAccount
import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))
from src.samples.bot_demo.adaptive_card import (
    create_table_adaptive_card,
    create_text_adaptive_card,
    create_error_adaptive_card,
    create_adaptive_card_attachment
)

from src.samples.bot_demo.config import DefaultConfig

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

# 全域變數用於存儲客戶端實例
_workspace_client = None
_genie_api = None

def get_databricks_clients():
    """延遲初始化 Databricks 客戶端"""
    global _workspace_client, _genie_api
    
    if _workspace_client is None:
        if not CONFIG.DATABRICKS_HOST or not CONFIG.DATABRICKS_TOKEN:
            raise ValueError("DATABRICKS_HOST 和 DATABRICKS_TOKEN 環境變數必須設定")
        
        _workspace_client = WorkspaceClient(
            host=CONFIG.DATABRICKS_HOST, 
            token=CONFIG.DATABRICKS_TOKEN
        )
        _genie_api = GenieAPI(_workspace_client.api_client)
    
    return _workspace_client, _genie_api


async def ask_genie(
    question: str, space_id: str, conversation_id: Optional[str] = None
) -> tuple[str, str]:
    try:
        # 取得 Databricks 客戶端
        workspace_client, genie_api = get_databricks_clients()
        
        loop = asyncio.get_running_loop()
        if conversation_id is None:
            # 建立新對話
            logger.info("建立新對話")
            initial_message = await loop.run_in_executor(
                None, genie_api.start_conversation_and_wait, space_id, question
            )
            conversation_id = initial_message.conversation_id
            logger.info(f"新對話 ID: {conversation_id}")
        else:
            # 在現有對話中繼續
            logger.info(f"繼續現有對話 ID: {conversation_id}")
            try:
                initial_message = await loop.run_in_executor(
                    None, genie_api.create_message_and_wait, space_id, conversation_id, question
                )
                logger.info("成功在現有對話中新增訊息")
            except Exception as e:
                logger.warning(f"無法在現有對話中繼續，建立新對話: {str(e)}")
                # 如果無法在現有對話中繼續，建立新對話
                initial_message = await loop.run_in_executor(
                    None, genie_api.start_conversation_and_wait, space_id, question
                )
                conversation_id = initial_message.conversation_id
                logger.info(f"建立新對話 ID: {conversation_id}")

        message_content = await loop.run_in_executor(
            None,
            genie_api.get_message,
            space_id,
            initial_message.conversation_id,
            initial_message.message_id,
        )
        
        if message_content.attachments:
            for attachment in message_content.attachments:
                if hasattr(attachment, 'attachment_id') and attachment.attachment_id:
                    try:
                        attachment_query_result = await loop.run_in_executor(
                            None,
                            genie_api.get_message_attachment_query_result,
                            space_id,
                            initial_message.conversation_id,
                            initial_message.message_id,
                            attachment.attachment_id,
                        )
                        
                        # 如果有查詢結果，回傳結構化資料
                        if attachment_query_result and attachment_query_result.statement_response:

                            # 回答描述
                            query_description = ""
                            if attachment.query and attachment.query.description:
                                query_description = attachment.query.description

                            # SQL 語句
                            sql_code = ""
                            if attachment.query and attachment.query.query:
                                sql_code = attachment.query.query

                            # 建立 Adaptive Card
                            adaptive_card = create_table_adaptive_card(
                                statement_response=attachment_query_result.statement_response, 
                                query_description=query_description,
                                sql_code=sql_code
                            )
                            return (
                                json.dumps({"adaptive_card": adaptive_card}),
                                initial_message.conversation_id,
                            )
                    except Exception as e:
                        logger.warning(f"無法取得 attachment 查詢結果 {attachment.attachment_id}: {str(e)}")
                
                # 如果沒有 attachment_id 或查詢失敗，回傳文字內容
                if attachment.text and attachment.text.content:
                    adaptive_card = create_text_adaptive_card(attachment.text.content)
                    return (
                        json.dumps({"adaptive_card": adaptive_card}),
                        initial_message.conversation_id,
                    )

        # 如果沒有 attachments，回傳基本訊息內容
        adaptive_card = create_text_adaptive_card(message_content.content or "沒有可用的回應內容")
        return json.dumps({"adaptive_card": adaptive_card}), initial_message.conversation_id
    
    except Exception as e:
        logger.error(f"Error in ask_genie: {str(e)}")
        error_card = create_error_adaptive_card("處理您的請求時發生錯誤。")
        return (
            json.dumps({"adaptive_card": error_card}),
            conversation_id if conversation_id else None,
        )


class MyBot(ActivityHandler):
    def __init__(self):
        self.conversation_ids: Dict[str, str] = {}

    async def on_message_activity(self, turn_context: TurnContext):
        question = turn_context.activity.text.strip()
        user_id = turn_context.activity.from_property.id
        
        # 檢查是否為重置命令
        if question.lower() in ['重新開始', 'reset', '新對話', 'new']:
            if user_id in self.conversation_ids:
                del self.conversation_ids[user_id]
            await turn_context.send_activity("對話已重新開始！請問您有什麼問題？")
            return
        
        conversation_id = self.conversation_ids.get(user_id, None)
        logger.info(f"使用者 {user_id} 的現有對話 ID: {conversation_id}")

        try:
            # 檢查是否已設定必要的環境變數
            if not CONFIG.DATABRICKS_HOST or not CONFIG.DATABRICKS_TOKEN or not CONFIG.DATABRICKS_SPACE_ID:
                await turn_context.send_activity(
                    "錯誤：請確保已設定 DATABRICKS_HOST、DATABRICKS_TOKEN 和 DATABRICKS_SPACE_ID 環境變數。"
                )
                return

            answer, new_conversation_id = await ask_genie(
                question, CONFIG.DATABRICKS_SPACE_ID, conversation_id
            )
            self.conversation_ids[user_id] = new_conversation_id
            logger.info(f"更新使用者 {user_id} 的對話 ID: {new_conversation_id}")

            answer_json = json.loads(answer)
            
            # 檢查是否有 Adaptive Card
            if "adaptive_card" in answer_json:
                # 建立 Adaptive Card 附件
                adaptive_card_attachment = create_adaptive_card_attachment(answer_json["adaptive_card"])
                message_with_card = MessageFactory.attachment(adaptive_card_attachment)
                await turn_context.send_activity(message_with_card)
            elif "error" in answer_json:
                # 處理錯誤訊息
                error_card = create_error_adaptive_card(answer_json["error"])
                adaptive_card_attachment = create_adaptive_card_attachment(error_card)
                message_with_card = MessageFactory.attachment(adaptive_card_attachment)
                await turn_context.send_activity(message_with_card)
            else:
                # 處理舊格式的回應（向後相容）
                message = answer_json.get("message", "沒有可用的回應")
                text_card = create_text_adaptive_card(message)
                adaptive_card_attachment = create_adaptive_card_attachment(text_card)
                message_with_card = MessageFactory.attachment(adaptive_card_attachment)
                await turn_context.send_activity(message_with_card)
            
        except json.JSONDecodeError:
            await turn_context.send_activity(
                "無法解碼伺服器回應。"
            )
        except ValueError as e:
            logger.error(f"設定錯誤: {str(e)}")
            await turn_context.send_activity(
                f"設定錯誤：{str(e)}"
            )
        except Exception as e:
            logger.error(f"處理訊息時發生錯誤: {str(e)}")
            await turn_context.send_activity(
                "處理您的請求時發生錯誤。請檢查您的 Databricks 設定。"
            )

    async def on_members_added_activity(
        self,
        members_added: List[ChannelAccount],
        turn_context: TurnContext
    ):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity("歡迎使用 Databricks Genie Bot！")
