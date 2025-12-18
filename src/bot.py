from typing import Dict, List
from botbuilder.core import ActivityHandler, TurnContext
from botbuilder.schema import ChannelAccount
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import FunctionTool, ToolSet
from fastapi import FastAPI

from src.core.logger_config import get_logger
from src.core.settings import get_settings
from utils.chart_tools import chart_to_base64
from src.utils.genie_tools import genie_manager

# 取得 logger 實例
logger = get_logger(__name__)


class MyBot(ActivityHandler):
    def __init__(self, app: FastAPI):
        """初始化 Bot

        Args:
            app: FastAPI 應用程式實例,用於存取 settings
        """
        self.thread_dict: Dict[str, str] = {}
        self.settings = get_settings(app)

        # 初始化 Azure 認證
        self.credential = DefaultAzureCredential(
            exclude_interactive_browser_credential=False
        )

        # 初始化 AI Project Client
        self.project_client = AIProjectClient(
            self.settings.azure_foundry["project_endpoint"], self.credential
        )

        self.agent_id = self.settings.azure_foundry["agent_id"]

        # 設定工具集
        self._setup_toolset()

    def _setup_toolset(self):
        """設定 AI Agent 工具集"""

        # 初始化 Genie
        genies = genie_manager.initialize(
            self.project_client,
            self.credential,
            self.settings.azure_foundry["connection_names"],
            self.settings.databricks["entra_id_audience_scope"],
        )

        toolset = ToolSet()
        toolset.add(FunctionTool(functions={genie_manager.ask_genie, chart_to_base64}))
        self.project_client.agents.enable_auto_function_calls(toolset)
        logger.info(f"工具集設定完成,可用的 Genie 連線: {list(genies.keys())}")

    async def on_message_activity(self, turn_context: TurnContext):
        """處理使用者訊息"""
        question = turn_context.activity.text.strip()
        user_id = turn_context.activity.from_property.id

        # 檢查是否為重置命令
        if question.lower() in ["重新開始", "reset", "新對話", "new"]:
            if user_id in self.thread_dict and self.thread_dict[user_id]:
                try:
                    self.project_client.agents.threads.delete(self.thread_dict[user_id])
                    logger.info(f"已刪除執行緒: {self.thread_dict[user_id]}")
                except Exception as e:
                    logger.warning(f"刪除執行緒失敗: {e}")
                self.thread_dict[user_id] = None
            await turn_context.send_activity("對話已重新開始！請問您有什麼問題？")
            return

        try:
            logger.info(f"使用者 {user_id}: {question}")

            # 建立或取得既有的執行緒
            thread_id = None
            if user_id not in self.thread_dict or not self.thread_dict[user_id]:
                thread = self.project_client.agents.threads.create()
                self.thread_dict[user_id] = thread.id
                thread_id = thread.id
                logger.info(f"建立新執行緒: {thread.id}")
            else:
                thread_id = self.thread_dict[user_id]
                logger.info(f"使用既有執行緒: {thread_id}")

            # 發送訊息
            self.project_client.agents.messages.create(
                thread_id=thread_id, role="user", content=question
            )

            # 執行代理程式
            run = self.project_client.agents.runs.create_and_process(
                thread_id=thread_id, agent_id=self.agent_id
            )
            logger.info(f"執行完成,狀態: {run.status}")

            # 取得回應
            messages = self.project_client.agents.messages.list(thread_id=thread_id)

            for msg in messages:
                if msg.role == "assistant":
                    if hasattr(msg, "content") and msg.content:
                        content_text = ""
                        if isinstance(msg.content, list):  # 如果內容是列表,提取文字部分
                            for content_item in msg.content:
                                if hasattr(content_item, "text"):
                                    if hasattr(content_item.text, "value"):
                                        content_text += content_item.text.value
                                    else:
                                        content_text += str(content_item.text)
                        else:
                            content_text = str(msg.content)

                        if content_text:
                            logger.info(f"助理回應: {content_text}")
                            await turn_context.send_activity(content_text)
                            return

            await turn_context.send_activity("抱歉,我無法取得回應。")

        except Exception as e:
            logger.error(f"處理訊息錯誤: {e}")
            await turn_context.send_activity(f"處理請求時發生錯誤: {e}")

    async def on_members_added_activity(
        self, members_added: List[ChannelAccount], turn_context: TurnContext
    ):
        """處理成員加入事件"""
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity("歡迎使用 Databricks Genie Bot！")
