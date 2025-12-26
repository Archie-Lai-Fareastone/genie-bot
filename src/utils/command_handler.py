"""
Bot 檢查使用者輸入的特殊命令並進行處理
包含重置對話與顯示說明
"""

from botbuilder.core import TurnContext
from azure.ai.projects import AIProjectClient
from src.core.logger_config import get_logger

logger = get_logger(__name__)


class CommandHandler:
    """處理特殊命令的處理器類別"""

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
            "• 說明 / help / 幫助 - 顯示此說明訊息\n\n"
            "直接輸入您的問題即可開始對話。"
        )
        await turn_context.send_activity(help_message)

    @staticmethod
    async def handle_greet(turn_context: TurnContext, bot_mode: str) -> None:
        """處理歡迎訊息

        Args:
            turn_context: Bot 的對話上下文
        """
        if bot_mode == "foundry":
            greetings = "👋 歡迎使用「大數據平台 Mobile 智靈」(Foundry Agent)！\n\n請輸入您要查詢的數據問題，或輸入 help 取得幫助"
        elif bot_mode == "genie":
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
    ) -> bool:
        """統一處理特殊命令

        Args:
            question: 使用者輸入的訊息
            turn_context: Bot 的對話上下文
            user_id: 使用者 ID
            thread_dict: 執行緒字典
            project_client: Azure AI Project 客戶端 (可選，僅 FoundryBot 需要)

        Returns:
            bool: 是否已處理特殊命令（True 表示已處理，False 表示非特殊命令）
        """
        # 檢查重置命令
        if self._is_reset_command(question):
            await self._handle_reset_command(
                turn_context, user_id, thread_dict, project_client
            )
            return True

        # 檢查說明命令
        if self._is_help_command(question):
            await self._handle_help_command(turn_context)
            return True

        # 非特殊命令
        return False
