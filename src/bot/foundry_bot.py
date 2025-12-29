from botbuilder.core import TurnContext, MessageFactory
from botbuilder.schema import Activity, ActivityTypes
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from azure.ai.agents.models import FunctionTool, ToolSet
from fastapi import FastAPI

from src.bot.base_bot import BaseBot
from src.core.logger_config import get_logger
from src.utils.genie_tools import genie_manager
from src.utils.response_format import get_agent_response_format
from src.utils.card_builder import convert_to_card
import json

# 取得 logger 實例
logger = get_logger(__name__)


class FoundryBot(BaseBot):
    def __init__(self, app: FastAPI):
        """初始化 Foundry Bot

        Args:
            app: FastAPI 應用程式實例,用於存取 settings
        """
        # 呼叫父類別初始化
        super().__init__(app)

        # 初始化 Azure 認證
        logger.info("======STEP 1: 正在初始化 Azure 認證======")
        self.credential = DefaultAzureCredential(
            exclude_interactive_browser_credential=False,
        )
        logger.info("Azure 認證已初始化")

        # 初始化 AI Project Client
        logger.info("======STEP 2: 正在初始化 AI Project Client======")
        self.project_client = AIProjectClient(
            self.settings.azure_foundry["project_endpoint"], self.credential
        )
        logger.info("AI Project Client 已初始化")

        self.agent_id = self.settings.azure_foundry["agent_id"]

        # 設定工具集
        logger.info("======STEP 3: 正在初始化 AI Agent 工具集======")
        try:
            self._setup_toolset()
        except Exception as e:
            logger.error(f"工具集設定失敗: {e}", exc_info=True)
            # 不要讓整個 Bot 初始化失敗，但要記錄錯誤

    def _setup_toolset(self):
        """設定 AI Agent 工具集"""
        try:
            # 初始化 Genie
            logger.info("開始初始化 Genie...")
            genies = genie_manager.initialize(
                self.project_client,
                self.credential,
                self.settings.azure_foundry["connection_names"],
                self.settings.databricks["entra_id_audience_scope"],
            )
            logger.info(f"Genie 初始化成功，連線數量: {len(genies)}")

            # 設定工具集
            logger.info("開始設定 ToolSet...")
            toolset = ToolSet()
            toolset.add(FunctionTool(functions={genie_manager.ask_genie}))
            self.project_client.agents.enable_auto_function_calls(toolset)
            logger.info(f"工具集設定完成,可用的 Genie 連線: {list(genies.keys())}")

        except Exception as e:
            logger.error(f"工具集設定過程中發生錯誤: {e}", exc_info=True)
            raise

    async def on_message_activity(self, turn_context: TurnContext):
        """處理使用者訊息"""
        question = turn_context.activity.text.strip()
        user_id = turn_context.activity.from_property.id

        # 檢查並處理特殊命令
        if await self.command_handler.handle_special_command(
            question, turn_context, user_id, self.thread_dict, self.project_client
        ):
            return

        # 顯示打字指示器
        await turn_context.send_activity(Activity(type=ActivityTypes.typing))

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

            # 發送訊息前再次顯示打字指示器
            await turn_context.send_activity(Activity(type=ActivityTypes.typing))
            
            # 發送訊息
            self.project_client.agents.messages.create(
                thread_id=thread_id, role="user", content=question
            )

            # 取得回應格式定義
            response_format = get_agent_response_format()

            # 執行代理程式前再次顯示打字指示器
            await turn_context.send_activity(Activity(type=ActivityTypes.typing))
            
            # 執行代理程式
            run = self.project_client.agents.runs.create_and_process(
                thread_id=thread_id,
                agent_id=self.agent_id,
                response_format=response_format,
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
                            try:
                                response_data = json.loads(content_text)
                                attachment = convert_to_card(response_data)
                                message = MessageFactory.attachment(attachment)
                                await turn_context.send_activity(message)
                                return
                            except json.JSONDecodeError as e:
                                logger.error(f"回應解析失敗: {e}")
                                await turn_context.send_activity(
                                    "回應內容格式錯誤，無法解析。"
                                )
                                return
                            except ValueError as e:
                                logger.error(f"卡片建立失敗: {e}")
                                await turn_context.send_activity(f"卡片建立錯誤: {e}")
                                return

            await turn_context.send_activity("抱歉,我無法取得回應。")

        except Exception as e:
            logger.error(f"處理訊息錯誤: {e}")
            await turn_context.send_activity(f"處理請求時發生錯誤: {e}")
