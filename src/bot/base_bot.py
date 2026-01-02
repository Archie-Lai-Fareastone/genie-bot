from typing import List
from botbuilder.core import ActivityHandler, TurnContext
from botbuilder.schema import ChannelAccount
from fastapi import FastAPI
from typing import Dict
from collections import OrderedDict
from datetime import datetime, timedelta
import asyncio

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
        self.settings = get_settings(app)
        self.bot_mode = self.settings.app["bot_mode"]
        self.command_handler = CommandHandler(bot_mode=self.bot_mode)

        # 儲存使用者執行緒字典
        # 使用 OrderedDict 追蹤最後使用時間
        self.thread_dict: Dict[str, str] = OrderedDict()
        self.thread_last_used: Dict[str, datetime] = {}

        # 設定參數 TODO: 可移至設定檔
        self.MAX_IDLE_TIME = timedelta(hours=24)  # 24小時未使用即清理
        self.MAX_THREADS = 100  # 最多保留100個執行緒
        self.CLEANUP_INTERVAL = 3600  # 每小時清理一次

        # 清理任務（延遲初始化）
        self._cleanup_task_handle = None

        logger.info("BaseBot 已初始化")

    def start_cleanup_task(self):
        """啟動背景清理任務 - 應在應用啟動時調用"""

        if self._cleanup_task_handle is None:
            try:
                self._cleanup_task_handle = asyncio.create_task(self._cleanup_task())
                logger.info("背景清理任務已啟動")
            except RuntimeError as e:
                logger.warning(f"無可用的事件迴圈，清理任務啟動失敗: {e}")

    async def on_message_activity(self, turn_context: TurnContext):
        """處理使用者訊息 - 子類別應該 override 此方法"""

        # 確保清理任務已啟動
        if self._cleanup_task_handle is None:
            self.start_cleanup_task()

        raise NotImplementedError("子類別必須實作 on_message_activity 方法")

    async def on_members_added_activity(
        self, members_added: List[ChannelAccount], turn_context: TurnContext
    ):
        """處理成員加入事件"""
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await self.command_handler.handle_greet(turn_context)
                logger.info(f"歡迎訊息已發送給使用者: {member.id}")

    async def _cleanup_task(self):
        """背景清理任務"""
        while True:
            try:
                await asyncio.sleep(self.CLEANUP_INTERVAL)
                await self._cleanup_inactive_threads()
            except Exception as e:
                logger.error(f"清理任務錯誤: {e}", exc_info=True)

    def _delete_thread(self, user_id: str, thread_id: str) -> bool:
        """刪除單個執行緒（Azure 和本地記錄）"""
        try:
            self.project_client.agents.threads.delete(thread_id)
            logger.info(f"已刪除執行緒: {thread_id} (使用者: {user_id})")
            return True
        except Exception as e:
            logger.warning(f"刪除執行緒失敗: {e}")
            return False
        finally:
            # 無論刪除是否成功，都清理本地記錄
            self.thread_dict.pop(user_id, None)
            self.thread_last_used.pop(user_id, None)

    async def _cleanup_inactive_threads(self):
        """清理不活躍的執行緒"""
        now = datetime.now()
        removed_count = 0

        # 找出並刪除過期的執行緒
        expired_users = [
            user_id
            for user_id, last_used in self.thread_last_used.items()
            if now - last_used > self.MAX_IDLE_TIME
        ]
        for user_id in expired_users:
            thread_id = self.thread_dict.get(user_id)
            if thread_id and self._delete_thread(user_id, thread_id):
                removed_count += 1

        # 如果超過最大數量，刪除最舊的
        while len(self.thread_dict) > self.MAX_THREADS:
            oldest_user_id = next(iter(self.thread_dict))
            thread_id = self.thread_dict[oldest_user_id]
            if self._delete_thread(oldest_user_id, thread_id):
                removed_count += 1

        if removed_count > 0:
            logger.info(f"清理完成，移除 {removed_count} 個執行緒")
