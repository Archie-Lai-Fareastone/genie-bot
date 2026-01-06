from typing import List
from botbuilder.core import ActivityHandler, TurnContext, MessageFactory
from botbuilder.schema import ChannelAccount, InvokeResponse
from botbuilder.schema.teams import FileConsentCardResponse
from fastapi import FastAPI
from typing import Dict
from collections import OrderedDict
from datetime import datetime, timedelta
import asyncio

from src.core.logger_config import get_logger
from src.core.settings import get_settings
from src.utils.command_handler import CommandHandler
from src.utils.file_handler import FileHandler, GraphService
from src.utils.card_builder import create_file_upload_confirmation_card

# 取得 logger 實例
logger = get_logger(__name__)


class BaseBot(ActivityHandler):
    """Bot 基底類別，提供共用的基本功能"""

    def __init__(self, app: FastAPI):
        """初始化 Bot

        Args:
            app: FastAPI 應用程式實例,用於存取 settings
        """
        super().__init__()
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

        # 初始化檔案處理器（如果有 Graph API 配置）
        self.file_handler = None
        try:
            graph_config = self.settings.graph_api
            if graph_config.get("client_id") and graph_config.get("client_secret"):
                graph_service = GraphService(
                    client_id=graph_config["client_id"],
                    client_secret=graph_config["client_secret"],
                    tenant_id=graph_config["tenant_id"],
                )
                self.file_handler = FileHandler(graph_service)
                logger.info("檔案處理器已初始化")
            else:
                logger.info("Graph API 配置不完整，跳過檔案處理器初始化")
        except (KeyError, AttributeError) as e:
            logger.info(f"未設定 Graph API 配置，跳過檔案處理器初始化: {e}")

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

    async def on_teams_file_consent_accept(
        self,
        turn_context: TurnContext,
        file_consent_card_response: FileConsentCardResponse,
    ) -> InvokeResponse:
        """
        處理使用者接受檔案上傳同意

        子類別可以覆寫此方法來自訂行為

        Args:
            turn_context: Bot 對話上下文
            file_consent_card_response: 檔案同意卡片回應

        Returns:
            InvokeResponse: 回應狀態
        """
        try:
            # 檢查是否有檔案處理器
            if not self.file_handler:
                logger.warning("檔案處理器未初始化，使用預設行為")
                await turn_context.send_activity(
                    f"已接收檔案: {file_consent_card_response.upload_info.name}"
                )
                return self._create_invoke_response()

            # 處理檔案上傳
            uploaded_file = await self.file_handler.handle_file_consent_accept(
                turn_context, file_consent_card_response
            )

            # 更新上傳狀態
            conversation_id = turn_context.activity.conversation.id
            upload_state = self.file_handler.update_upload_state(
                conversation_id, uploaded_file
            )

            # 嘗試下載檔案內容（驗證存取權限）
            try:
                content = await self.file_handler.download_file(
                    uploaded_file.download_url
                )
                # 更新實際檔案大小（如果之前未知）
                if uploaded_file.size == 0:
                    uploaded_file.size = len(content)
                logger.info(
                    f"成功下載檔案: {uploaded_file.name}, "
                    f"大小: {len(content)} bytes"
                )
            except Exception as download_error:
                logger.error(f"下載檔案時發生錯誤: {download_error}", exc_info=True)
                await turn_context.send_activity(
                    f"檔案上傳成功，但無法下載內容: {download_error}"
                )
                return self._create_invoke_response(200)

            # 檢查是否所有檔案都已收到
            if upload_state.status == "completed":
                # 準備檔案資訊
                files_info = [
                    {"name": f.name, "size": f.size, "content_type": f.content_type}
                    for f in upload_state.received_files
                ]

                # 發送 Adaptive Card 確認
                confirmation_card = create_file_upload_confirmation_card(files_info)
                message = MessageFactory.attachment(confirmation_card)
                await turn_context.send_activity(message)

                logger.info(
                    f"已發送檔案上傳確認卡片，"
                    f"共 {len(upload_state.received_files)} 個檔案"
                )

                # 清理狀態
                self.file_handler.clear_upload_state(conversation_id)
            else:
                # 尚未收到所有檔案，發送進度訊息
                await turn_context.send_activity(
                    f"已接收檔案: {uploaded_file.name} "
                    f"({len(upload_state.received_files)}/{upload_state.expected_files})"
                )

            return self._create_invoke_response()

        except Exception as e:
            logger.error(f"處理檔案同意接受時發生錯誤: {e}", exc_info=True)
            await turn_context.send_activity(f"處理檔案上傳時發生錯誤: {e}")
            return self._create_invoke_response(500)

    async def on_teams_file_consent_decline(
        self,
        turn_context: TurnContext,
        file_consent_card_response: FileConsentCardResponse,
    ) -> InvokeResponse:
        """
        處理使用者拒絕檔案上傳同意

        子類別可以覆寫此方法來自訂行為

        Args:
            turn_context: Bot 對話上下文
            file_consent_card_response: 檔案同意卡片回應

        Returns:
            InvokeResponse: 回應狀態
        """
        try:
            state = None

            # 使用檔案處理器處理（如果可用）
            if self.file_handler:
                state = await self.file_handler.handle_file_consent_decline(
                    turn_context, file_consent_card_response
                )
            else:
                # 預設行為
                logger.info(
                    f"使用者拒絕檔案上傳: "
                    f"{file_consent_card_response.context.get('filename', 'unknown')}"
                )
                await turn_context.send_activity("已取消檔案上傳。")

            # 若所有檔案都已處理（接受或拒絕），提供收尾訊息
            if self.file_handler and state and state.status == "completed":
                conversation_id = turn_context.activity.conversation.id
                if state.received_files:
                    files_info = [
                        {
                            "name": f.name,
                            "size": f.size,
                            "content_type": f.content_type,
                        }
                        for f in state.received_files
                    ]
                    confirmation_card = create_file_upload_confirmation_card(files_info)
                    await turn_context.send_activity(
                        MessageFactory.attachment(confirmation_card)
                    )
                else:
                    await turn_context.send_activity(
                        "此次上傳流程已取消，未收到任何檔案。"
                    )

                self.file_handler.clear_upload_state(conversation_id)

            return self._create_invoke_response()

        except Exception as e:
            logger.error(f"處理檔案同意拒絕時發生錯誤: {e}", exc_info=True)
            return self._create_invoke_response(500)

    def _create_invoke_response(self, status: int = 200) -> InvokeResponse:
        """
        建立 InvokeResponse

        Args:
            status: HTTP 狀態碼

        Returns:
            InvokeResponse
        """
        return InvokeResponse(status=status)

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
