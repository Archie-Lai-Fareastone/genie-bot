"""
Bot 檢查使用者輸入的特殊命令並進行處理
包含重置對話與顯示說明
"""

import re
from typing import Optional
from botbuilder.core import TurnContext
from azure.ai.projects import AIProjectClient
from src.core.logger_config import get_logger

logger = get_logger(__name__)


class CommandHandler:
    """處理特殊命令的處理器類別"""

    MAX_UPLOAD_FILES = 5

    def __init__(self, bot_mode: str):
        self.bot_mode = bot_mode

    @staticmethod
    def _is_reset_command(question: str) -> bool:
        """檢查訊息是否為重置命令

        Args:
            question: 使用者輸入的訊息

        Returns:
            bool: 是否為重置命令
        """
        return question.lower() in ["重新開始", "reset", "新對話", "new"]

    @staticmethod
    def _is_help_command(question: str) -> bool:
        """檢查訊息是否為說明命令

        Args:
            question: 使用者輸入的訊息

        Returns:
            bool: 是否為說明命令
        """
        return question.lower() in ["說明", "help", "幫助"]

    @staticmethod
    def _is_greet_command(question: str) -> bool:
        """檢查是否為歡迎指令

        Args:
            question: 使用者輸入的訊息

        Returns:
            bool: 是否為說明命令
        """
        return question.lower() in ["hello", "hi", "你好", "您好"]

    @staticmethod
    def _is_upload_command(question: str) -> bool:
        """檢查是否包含上傳關鍵字

        Args:
            question: 使用者輸入的訊息

        Returns:
            bool: 是否為上傳命令
        """
        upload_keywords = ["上傳", "upload"]
        return any(keyword in question.lower() for keyword in upload_keywords)

    @staticmethod
    async def _handle_reset_command(
        turn_context: TurnContext,
        user_id: str,
        thread_dict: dict,
        project_client: AIProjectClient = None,
    ) -> None:
        """處理重置命令

        Args:
            turn_context: Bot 的對話上下文
            user_id: 使用者 ID
            thread_dict: 執行緒字典
            project_client: Azure AI Project 客戶端 (可選，僅 FoundryBot 需要)
        """
        if user_id in thread_dict and thread_dict[user_id]:
            # 如果是 FoundryBot，需要透過 API 刪除執行緒
            if project_client:
                try:
                    project_client.agents.threads.delete(thread_dict[user_id])
                    logger.info(f"已刪除執行緒: {thread_dict[user_id]}")
                except Exception as e:
                    logger.warning(f"刪除執行緒失敗: {e}")
            thread_dict[user_id] = None
        await turn_context.send_activity("對話已重新開始！請問您有什麼問題？")

    @staticmethod
    async def _handle_help_command(turn_context: TurnContext) -> None:
        """處理說明命令

        Args:
            turn_context: Bot 的對話上下文
        """
        help_message = (
            "可用命令：\n\n"
            "• 重新開始 / reset / 新對話 / new - 重新開始對話\n\n"
            "• 上傳 / upload - 上傳檔案到 Bot\n\n"
            "• 說明 / help / 幫助 - 顯示此說明訊息\n\n"
            "直接輸入您的問題即可開始對話。"
        )
        await turn_context.send_activity(help_message)

    @staticmethod
    def _extract_upload_count(question: str) -> Optional[int]:
        """嘗試從使用者輸入解析欲上傳檔案數量"""

        matches = re.findall(r"(\d+)", question)
        if not matches:
            return None

        try:
            value = int(matches[0])
            return value if value > 0 else None
        except ValueError:
            return None

    async def _handle_upload_command(
        self,
        turn_context: TurnContext,
        file_handler=None,
        requested_files: Optional[int] = None,
    ) -> None:
        """處理上傳命令

        Args:
            turn_context: Bot 的對話上下文
            file_handler: FileHandler 實例（如果可用）
        """
        if not file_handler:
            await turn_context.send_activity(
                "抱歉，檔案上傳功能目前無法使用。請聯絡系統管理員。"
            )
            return

        conversation_id = turn_context.activity.conversation.id

        existing_state = file_handler.get_upload_state(conversation_id)
        if existing_state and existing_state.status == "pending":
            await turn_context.send_activity(
                "已經有一個進行中的檔案批次，請在完成後再啟動新的上傳流程。"
            )
            return

        max_files = getattr(file_handler, "max_files_per_batch", self.MAX_UPLOAD_FILES)

        expected_files = requested_files or 1
        expected_files = max(1, min(expected_files, max_files))

        file_handler.create_upload_state(conversation_id, expected_files)

        await turn_context.send_activity(
            f"請上傳 {expected_files} 個檔案（支援 PDF、Word、Excel 等格式）。"
        )

        for idx in range(expected_files):
            filename = f"user_upload_{idx + 1}.dat"
            description = f"檔案 {idx + 1}/{expected_files}：請選擇要分享的檔案"
            await file_handler.send_file_consent_card(
                turn_context,
                filename=filename,
                description=description,
            )

        logger.info(f"已發送 {expected_files} 張檔案上傳同意卡片")

    async def handle_greet(self, turn_context: TurnContext) -> None:
        """處理歡迎訊息

        Args:
            turn_context: Bot 的對話上下文
        """
        if self.bot_mode == "foundry":
            greetings = "👋 歡迎使用「大數據平台 Mobile 智靈」(Foundry Agent)！\n\n請輸入您要查詢的數據問題，或輸入 help 取得幫助"
        elif self.bot_mode == "genie":
            greetings = "👋 歡迎使用「大數據平台 Mobile 智靈」(Databricks Genie)！\n\n請輸入您要查詢的數據問題，或輸入 help 取得幫助"
        else:
            greetings = "歡迎使用本服務！請聯絡管理員設定正確的 Bot 類型。"
        await turn_context.send_activity(greetings)

    async def handle_special_command(
        self,
        question: str,
        turn_context: TurnContext,
        user_id: str,
        thread_dict: dict,
        project_client: AIProjectClient = None,
        file_handler=None,
    ) -> bool:
        """統一處理特殊命令

        Args:
            question: 使用者輸入的訊息
            turn_context: Bot 的對話上下文
            user_id: 使用者 ID
            thread_dict: 執行緒字典
            project_client: Azure AI Project 客戶端 (可選，僅 FoundryBot 需要)
            file_handler: FileHandler 實例 (可選，用於檔案上傳)

        Returns:
            bool: 是否已處理特殊命令（True 表示已處理，False 表示非特殊命令）
        """
        normalized_question = (question or "").strip()

        # 檢查上傳命令
        if self._is_upload_command(normalized_question):
            requested_count = self._extract_upload_count(normalized_question)
            await self._handle_upload_command(
                turn_context, file_handler, requested_count
            )
            return True

        # 檢查歡迎命令
        if self._is_greet_command(normalized_question):
            await self.handle_greet(turn_context)
            return True

        # 檢查重置命令
        if self._is_reset_command(normalized_question):
            await self._handle_reset_command(
                turn_context, user_id, thread_dict, project_client
            )
            return True

        # 檢查說明命令
        if self._is_help_command(normalized_question):
            await self._handle_help_command(turn_context)
            return True

        # 非特殊命令
        return False
