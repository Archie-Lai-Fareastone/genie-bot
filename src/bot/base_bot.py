from typing import Dict, List
from botbuilder.core import ActivityHandler, TurnContext
from botbuilder.schema import ChannelAccount
from fastapi import FastAPI

from src.core.logger_config import get_logger
from src.core.settings import get_settings
from src.utils.command_handler import CommandHandler

# 取得 logger 實例
logger = get_logger(__name__)


class BaseBot(ActivityHandler):
    """Bot 基底類別，提供共用的基本功能"""

    def __init__(self, app: FastAPI):
        """初始化 Bot

        Args:
            app: FastAPI 應用程式實例,用於存取 settings
        """
        self.thread_dict: Dict[str, str] = {}
        self.settings = get_settings(app)
        self.command_handler = CommandHandler()
        logger.info("BaseBot 已初始化")

    async def on_message_activity(self, turn_context: TurnContext):
        """處理使用者訊息 - 子類別應該 override 此方法"""
        raise NotImplementedError("子類別必須實作 on_message_activity 方法")

    async def on_members_added_activity(
        self, members_added: List[ChannelAccount], turn_context: TurnContext
    ):
        """處理成員加入事件"""
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await self.command_handler.handle_greet(turn_context, bot_mode=self.settings.app["bot_mode"])
                logger.info(f"歡迎訊息已發送給使用者: {member.id}")
