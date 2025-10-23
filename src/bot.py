import logging
from typing import Dict, List, Optional
import asyncio
import os
from dotenv import load_dotenv
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.dashboards import GenieAPI
from botbuilder.core import ActivityHandler, TurnContext, MessageFactory
from botbuilder.schema import ChannelAccount

from src.utils.adaptive_card import (
    create_response_card,
    create_error_card,
    ColumnSchema
)


# 載入環境變數
load_dotenv()

DATABRICKS_HOST = os.environ.get("DATABRICKS_HOST", "")
DATABRICKS_TOKEN = os.environ.get("DATABRICKS_TOKEN", "")
DATABRICKS_SPACE_ID = os.environ.get("DATABRICKS_SPACE_ID", "")

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
        if not DATABRICKS_HOST or not DATABRICKS_TOKEN:
            raise ValueError("DATABRICKS_HOST 和 DATABRICKS_TOKEN 環境變數必須設定")
        
        _workspace_client = WorkspaceClient(
            host=DATABRICKS_HOST, 
            token=DATABRICKS_TOKEN
        )
        _genie_api = GenieAPI(_workspace_client.api_client)
    
    return _workspace_client, _genie_api


async def ask_genie(
    question: str, space_id: str, conversation_id: Optional[str] = None
) -> tuple[str, str]:
    try:
        # 取得 Databricks 客戶端
        workspace_client, genie_api = get_databricks_clients()

        # genie 回覆資料
        response_text = ""
        query_description = ""
        sql_code = ""
        schema_columns = []
        data_array = []
        
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

                # 如果附件有文字內容，累加到回應文本
                if hasattr(attachment, 'text') and attachment.text:
                    response_text += attachment.text.content + "\n"

                # 如果附件有 attachment_id，則查詢結構化資料
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
                            if attachment.query and attachment.query.description:
                                query_description = attachment.query.description

                            # SQL 語句
                            if attachment.query and attachment.query.query:
                                sql_code = attachment.query.query

                            # 轉換欄位結構為統一格式
                            statement_response = attachment_query_result.statement_response
                            schema_columns = [
                                ColumnSchema(
                                    name=col.name,
                                    type=col.type_name.value if hasattr(col.type_name, 'value') else str(col.type_name)
                                )
                                for col in statement_response.manifest.schema.columns
                            ]

                            data_array = statement_response.result.data_array

                    except Exception as e:
                        logger.warning(f"無法取得 attachment 查詢結果 {attachment.attachment_id}: {str(e)}")

        response_card = create_response_card(
            schema_columns=schema_columns,
            data_array=data_array,
            total_row_count=statement_response.manifest.total_row_count,
            query_description=query_description or response_text or "沒有可用的回應內容",
            sql_code=sql_code
        )

        return (response_card, initial_message.conversation_id)
    
    except Exception as e:
        logger.error(f"Error in ask_genie: {str(e)}")
        error_card = create_error_card("處理您的請求時發生錯誤。")
        return (
            error_card,
            conversation_id if conversation_id else None,
        )


class MyBot(ActivityHandler):
    def __init__(self):
        self.conversation_ids: Dict[str, str] = {}

    async def on_turn(self, turn_context: TurnContext):
        logger.info(f"Bot on_turn 被呼叫，活動類型: {turn_context.activity.type}")
        await super().on_turn(turn_context)

    async def on_message_activity(self, turn_context: TurnContext):
        question = turn_context.activity.text.strip()
        user_id = turn_context.activity.from_property.id
        
        logger.info(f"收到使用者 {user_id} 的訊息: {question}")
        
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
            logger.info(f"檢查環境變數 - HOST: {'已設定' if DATABRICKS_HOST else '未設定'}, "
                       f"TOKEN: {'已設定' if DATABRICKS_TOKEN else '未設定'}, "
                       f"SPACE_ID: {'已設定' if DATABRICKS_SPACE_ID else '未設定'}")
            
            if not DATABRICKS_HOST or not DATABRICKS_TOKEN or not DATABRICKS_SPACE_ID:
                error_msg = "錯誤：請確保已設定 DATABRICKS_HOST、DATABRICKS_TOKEN 和 DATABRICKS_SPACE_ID 環境變數。"
                logger.error(error_msg)
                await turn_context.send_activity(error_msg)
                return

            logger.info(f"開始呼叫 ask_genie，問題: {question}")
            response_card, new_conversation_id = await ask_genie(
                question, DATABRICKS_SPACE_ID, conversation_id
            )
            self.conversation_ids[user_id] = new_conversation_id
            logger.info(f"更新使用者 {user_id} 的對話 ID: {new_conversation_id}")

            message_activity = MessageFactory.attachment(response_card)
            logger.info("發送 adaptive card 回應")
            await turn_context.send_activity(message_activity)
            
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
