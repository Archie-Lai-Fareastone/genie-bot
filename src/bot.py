import json
from typing import Dict, List
from botbuilder.core import ActivityHandler, TurnContext
from botbuilder.schema import ChannelAccount
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import FunctionTool, ToolSet
from databricks.sdk import WorkspaceClient
from databricks_ai_bridge.genie import Genie
from fastapi import FastAPI

from src.core.logger_config import get_logger
from src.core.settings import get_settings
from src.utils.generate_chart_base64 import chart_to_base64

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

        # 初始化 Genie
        self._init_genie()

        # 設定工具集
        self._setup_toolset()

    def _init_genie(self):
        """初始化多個 Genie 客戶端"""
        self.genies = {}

        for connection_name in self.settings.azure_foundry["connection_names"]:
            connection = self.project_client.connections.get(connection_name)
            genie_space_id = connection.metadata["genie_space_id"]

            databricks_client = WorkspaceClient(
                host=connection.target,
                token=self.credential.get_token(
                    self.settings.databricks["entra_id_audience_scope"]
                ).token,
            )

            self.genies[connection_name] = Genie(
                genie_space_id, client=databricks_client
            )
            logger.info(
                f"Genie 初始化完成,Connection: {connection_name}, Space ID: {genie_space_id}"
            )

        logger.info(
            f"總共初始化了 {len(self.genies)} 個 Genie 客戶端: {list(self.genies.keys())}"
        )

    def ask_genie(self, connection_name: str, question: str) -> str:
        """向指定的 Genie 提問

        Args:
            connection_name: Genie 連線名稱
            question: 要詢問的問題

        Returns:
            JSON 格式的回應，包含 connection_name, query, result, description 或 error
        """
        try:
            if connection_name not in self.genies:
                available = ", ".join(self.genies.keys())
                logger.warning(
                    f"無效的 connection_name: {connection_name}。可用選項: {available}"
                )
                return json.dumps(
                    {
                        "error": f"無效的 connection_name: {connection_name}。可用的選項: {available}"
                    }
                )

            logger.info(f"使用 Genie [{connection_name}] 處理問題: {question}")
            response = self.genies[connection_name].ask_question(question)

            result = {
                "connection_name": connection_name,
                "query": response.query,
                "result": response.result,
                "description": response.description,
            }
            logger.info(f"Genie [{connection_name}] 回應成功")
            return json.dumps(result)

        except Exception as e:
            logger.error(f"Genie [{connection_name}] 提問失敗: {e}", exc_info=True)
            return json.dumps({"error": str(e)})

    def _setup_toolset(self):
        """設定 AI Agent 工具集"""
        toolset = ToolSet()
        toolset.add(FunctionTool(functions={self.ask_genie, chart_to_base64}))
        self.project_client.agents.enable_auto_function_calls(toolset)
        logger.info(f"工具集設定完成,可用的 Genie 連線: {list(self.genies.keys())}")

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

            # 找到最新的助理回應（messages 已按時間倒序排列）
            for msg in messages:
                if msg.role == "assistant":
                    # 處理訊息內容
                    if hasattr(msg, "content") and msg.content:
                        content_text = ""
                        if isinstance(msg.content, list):
                            # 如果內容是列表,提取文字部分
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
