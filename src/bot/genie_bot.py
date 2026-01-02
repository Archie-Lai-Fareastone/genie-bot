"""
Genie Bot 模組

此模組負責與 Databricks Genie API 互動，並處理使用者訊息。

FIXME:
- 尚未實作同一 session 繼續對話的功能。
"""

import asyncio
from typing import Optional
from botbuilder.core import TurnContext, MessageFactory
from botbuilder.schema import Activity, ActivityTypes
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.dashboards import GenieAPI
from fastapi import FastAPI

from src.bot.base_bot import BaseBot
from src.core.logger_config import get_logger
from src.utils.card_builder import convert_to_card

logger = get_logger(__name__)


class GenieBot(BaseBot):
    def __init__(self, app: FastAPI):
        """初始化 Genie Bot

        Args:
            app: FastAPI 應用程式實例,用於存取 settings
        """
        super().__init__(app)
        self.bot_mode = "genie"

        # 初始化 Databricks 客戶端
        logger.info("======正在初始化 Databricks 客戶端======")
        self.workspace_client = WorkspaceClient(
            host=self.settings.databricks["host"],
            token=self.settings.databricks["token"],
        )
        self.genie_api = GenieAPI(self.workspace_client.api_client)
        self.genie_space_id = self.settings.databricks["genie_space_id"]
        logger.info("Databricks Genie 客戶端已初始化")

        # 儲存對話 ID
        self.conversation_dict = {}

    async def ask_genie(
        self, question: str, conversation_id: Optional[str] = None
    ) -> tuple[str, str, str]:
        """呼叫 Genie API

        Args:
            question: 使用者問題
            conversation_id: 對話 ID (可選)

        Returns:
            tuple: (message_content, conversation_id, message_id)
        """
        try:
            loop = asyncio.get_running_loop()

            if conversation_id is None:
                initial_message = await loop.run_in_executor(
                    None,
                    self.genie_api.start_conversation_and_wait,
                    self.genie_space_id,
                    question,
                )
            else:
                initial_message = await loop.run_in_executor(
                    None,
                    self.genie_api.create_message_and_wait,
                    self.genie_space_id,
                    conversation_id,
                    question,
                )

            # 取得訊息內容
            message_content = await loop.run_in_executor(
                None,
                self.genie_api.get_message,
                self.genie_space_id,
                initial_message.conversation_id,
                initial_message.message_id,
            )

            logger.info(f"Genie 回應: attachments={message_content.attachments}")

            return (
                message_content,
                initial_message.conversation_id,
                initial_message.message_id,
            )
        except Exception as e:
            logger.error(f"Error in ask_genie: {e}")
            raise

    async def on_message_activity(self, turn_context: TurnContext):
        """處理使用者訊息"""
        question = turn_context.activity.text.strip()
        user_id = turn_context.activity.from_property.id

        # 檢查並處理特殊命令
        if await self.command_handler.handle_special_command(
            question, turn_context, user_id, self.conversation_dict, None
        ):
            return

        # 顯示打字指示器
        await turn_context.send_activity(Activity(type=ActivityTypes.typing))

        try:
            logger.info(f"使用者 {user_id}: {question}")

            # 取得或建立對話
            conversation_id = self.conversation_dict.get(user_id)

            # 呼叫 Genie API 前再次顯示打字指示器
            await turn_context.send_activity(Activity(type=ActivityTypes.typing))

            # 呼叫 Genie API
            message_content, new_conversation_id, message_id = await self.ask_genie(
                question, conversation_id
            )

            # 儲存對話 ID
            self.conversation_dict[user_id] = new_conversation_id

            # 準備卡片資料
            cards = []

            # 處理附件
            if message_content.attachments:
                for attachment in message_content.attachments:
                    # 優先處理文字回應
                    if hasattr(attachment, "text") and attachment.text:
                        if (
                            hasattr(attachment.text, "content")
                            and attachment.text.content
                        ):
                            cards.append(
                                {
                                    "card_type": "text",
                                    "content": attachment.text.content,
                                }
                            )

                    # 處理查詢結果
                    elif hasattr(attachment, "query") and attachment.query:
                        query = attachment.query

                        # 顯示查詢描述
                        if hasattr(query, "description") and query.description:
                            cards.append(
                                {
                                    "card_type": "text",
                                    "content": f"**查詢說明**: {query.description}",
                                }
                            )

                        # 顯示 SQL 查詢
                        if hasattr(query, "query") and query.query:
                            cards.append(
                                {
                                    "card_type": "sql",
                                    "content": query.query,
                                }
                            )

                        # 取得並顯示查詢結果
                        if hasattr(query, "statement_id") and query.statement_id:
                            try:
                                # 處理查詢結果前再次顯示打字指示器
                                await turn_context.send_activity(
                                    Activity(type=ActivityTypes.typing)
                                )

                                loop = asyncio.get_running_loop()
                                statement_result = await loop.run_in_executor(
                                    None,
                                    self.workspace_client.statement_execution.get_statement,
                                    query.statement_id,
                                )

                                if statement_result and statement_result.result:
                                    result = statement_result.result
                                    manifest = statement_result.manifest

                                    # 從 manifest.schema 取得欄位名稱
                                    if (
                                        manifest
                                        and manifest.schema
                                        and manifest.schema.columns
                                    ):
                                        headers = [
                                            col.name for col in manifest.schema.columns
                                        ]

                                        # 從 result.data_array 取得資料列
                                        rows = []
                                        if (
                                            hasattr(result, "data_array")
                                            and result.data_array
                                        ):
                                            for row_data in result.data_array:
                                                row = [
                                                    (
                                                        str(cell)
                                                        if cell is not None
                                                        else ""
                                                    )
                                                    for cell in row_data
                                                ]
                                                rows.append(row)

                                        if headers and rows:
                                            cards.append(
                                                {
                                                    "card_type": "table",
                                                    "headers": headers,
                                                    "rows": rows,
                                                }
                                            )
                            except Exception as e:
                                logger.error(f"取得查詢結果失敗: {e}", exc_info=True)
                                cards.append(
                                    {
                                        "card_type": "text",
                                        "content": f"查詢執行成功，但無法取得結果: {e}",
                                    }
                                )

            # 如果沒有任何 attachment，才使用 message_content.content
            if not cards and message_content.content:
                cards.append({"card_type": "text", "content": message_content.content})

            # 使用 convert_to_card 建立卡片
            response_data = {"cards": cards}
            attachment = convert_to_card(response_data)
            message = MessageFactory.attachment(attachment)
            await turn_context.send_activity(message)

        except Exception as e:
            logger.error(f"處理訊息錯誤: {e}", exc_info=True)
            await turn_context.send_activity(f"處理請求時發生錯誤: {e}")
