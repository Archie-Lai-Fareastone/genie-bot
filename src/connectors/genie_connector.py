"""
Databricks Genie Space Connector

此模組提供與 Databricks Genie Space 互動的連接器類別。
"""

import os
import asyncio
from typing import Optional, Tuple
from dotenv import load_dotenv
from databricks.sdk import WorkspaceClient
from databricks.sdk.service.dashboards import GenieAPI

from utils.adaptive_card import (
    create_response_card,
    create_error_card,
    create_text_card,
    ColumnSchema
)
from src.utils.logger_config import get_logger
from src.connectors.response import ConnectorResponse

# 載入環境變數
load_dotenv()

# 取得 logger 實例
logger = get_logger(__name__)


class GenieConnector:
    """
    Databricks Genie Space 連接器
    
    負責處理所有與 Databricks Genie Space 相關的操作，包括：
    - Databricks 客戶端初始化
    - Genie Space 選擇和管理
    - 問題查詢和回應處理
    """
    
    def __init__(self):
        """初始化 GenieConnector"""
        self.databricks_host = os.environ.get("DATABRICKS_HOST", "")
        self.databricks_token = os.environ.get("DATABRICKS_TOKEN", "")
        self._workspace_client: Optional[WorkspaceClient] = None
        self._genie_api: Optional[GenieAPI] = None
        self._space_id: Optional[str] = None
        self.response: ConnectorResponse = ConnectorResponse()
        
        logger.info("GenieConnector 已初始化")
    
    def _setup_client(self) -> Tuple[WorkspaceClient, GenieAPI]:
        """
        延遲初始化 Databricks 客戶端
        
        Returns:
            Tuple[WorkspaceClient, GenieAPI]: Workspace 客戶端和 Genie API 實例
            
        Raises:
            ValueError: 當環境變數未設定時
        """
        if self._workspace_client is None:
            if not self.databricks_host or not self.databricks_token:
                raise ValueError("DATABRICKS_HOST 和 DATABRICKS_TOKEN 環境變數必須設定")
            
            self._workspace_client = WorkspaceClient(
                host=self.databricks_host,
                token=self.databricks_token
            )
            self._genie_api = GenieAPI(self._workspace_client.api_client)
            logger.info("Databricks 客戶端已初始化")
    
    def set_space_id(self, space_id: str) -> None:
        self._space_id = space_id
        logger.info(f"設定 Genie Space ID: {space_id}")
    
    def get_space_id(self) -> Optional[str]:
        return self._space_id
    
    async def _process_message_attachments(
        self,
        message_content,
        conversation_id: str,
        message_id: str
    ) -> Optional[Tuple[str, str]]:
        """
        處理訊息附件內容
        
        Args:
            message_content: 訊息內容物件
            conversation_id: 對話 ID
            message_id: 訊息 ID
            
        Returns:
            Optional[Tuple[str, str]]: 如果需要提前回傳，則回傳 (回應卡片, 對話 ID)，否則回傳 None
        """
        if not message_content.attachments:
            return None
        
        loop = asyncio.get_running_loop()
        
        for attachment in message_content.attachments:
            # 處理文字內容
            if hasattr(attachment, 'text') and attachment.text:
                if self.response.response_text is None:
                    self.response.response_text = ""
                self.response.response_text += attachment.text.content + "\n"
            
            # 處理結構化資料
            if hasattr(attachment, 'attachment_id') and attachment.attachment_id:
                try:
                    attachment_query_result = await loop.run_in_executor(
                        None,
                        self._genie_api.get_message_attachment_query_result,
                        self._space_id,
                        conversation_id,
                        message_id,
                        attachment.attachment_id,
                    )
                    
                    if attachment_query_result and attachment_query_result.statement_response:
                        # 儲存查詢描述
                        if attachment.query and attachment.query.description:
                            self.response.query_description = attachment.query.description
                        
                        # 儲存 SQL 語句
                        if attachment.query and attachment.query.query:
                            self.response.sql_code = attachment.query.query
                        
                        # 轉換欄位結構
                        statement_response = attachment_query_result.statement_response
                        self.response.schema_columns = [
                            ColumnSchema(
                                name=col.name,
                                type=col.type_name.value if hasattr(col.type_name, 'value') else str(col.type_name)
                            )
                            for col in statement_response.manifest.schema.columns
                        ]
                        
                        self.response.data_array = statement_response.result.data_array
                        self.response.total_row_count = statement_response.manifest.total_row_count
                
                except Exception as e:
                    logger.warning(f"無法取得 attachment 查詢結果 {attachment.attachment_id}: {str(e)}")
                    # 回傳純文字內容
                    if self.response.response_text:
                        return create_text_card(self.response.response_text), conversation_id
        
        return None
    
    async def _create_or_continue_conversation(
        self,
        question: str,
        conversation_id: Optional[str]
    ) -> Tuple[any, str]:
        """
        建立新對話或繼續現有對話
        
        Args:
            question: 要詢問的問題
            conversation_id: 現有對話 ID（可選）
            
        Returns:
            Tuple[any, str]: (訊息物件, 對話 ID)
        """
        loop = asyncio.get_running_loop()
        
        if conversation_id is None:
            # 建立新對話
            logger.info("建立新對話")
            initial_message = await loop.run_in_executor(
                None, self._genie_api.start_conversation_and_wait, self._space_id, question
            )
            conversation_id = initial_message.conversation_id
            logger.info(f"新對話 ID: {conversation_id}")
        else:
            # 在現有對話中繼續
            logger.info(f"繼續現有對話 ID: {conversation_id}")
            try:
                initial_message = await loop.run_in_executor(
                    None, self._genie_api.create_message_and_wait, 
                    self._space_id, conversation_id, question
                )
                logger.info("成功在現有對話中新增訊息")
            except Exception as e:
                logger.warning(f"無法在現有對話中繼續，建立新對話: {str(e)}")
                initial_message = await loop.run_in_executor(
                    None, self._genie_api.start_conversation_and_wait, 
                    self._space_id, question
                )
                conversation_id = initial_message.conversation_id
                logger.info(f"建立新對話 ID: {conversation_id}")
        
        return initial_message, conversation_id
    
    async def ask_question(
        self,
        question: str,
        conversation_id: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Args:
            question: 要詢問的問題
            conversation_id: 現有對話 ID（可選）
            
        Returns:
            Tuple[str, str]: (回應卡片, 對話 ID)
        """
        if not self.get_space_id():
            raise ValueError("請先設定 Genie Space ID")
        
        try:
            self._setup_client()
            self.response.reset()
            
            # 建立或繼續對話
            initial_message, conversation_id = await self._create_or_continue_conversation(
                question, conversation_id
            )
            
            # 取得訊息內容
            loop = asyncio.get_running_loop()
            message_content = await loop.run_in_executor(
                None,
                self._genie_api.get_message,
                self._space_id,
                initial_message.conversation_id,
                initial_message.message_id,
            )
            
            # 處理附件
            early_return = await self._process_message_attachments(
                message_content,
                initial_message.conversation_id,
                initial_message.message_id
            )
            # 回傳純文字內容
            if early_return:
                return early_return
            
            # 建立回應卡片
            response_card = create_response_card(self.response)

            return (response_card, initial_message.conversation_id)
        
        except Exception as e:
            logger.error(f"GenieConnector.ask_question 發生錯誤: {str(e)}")
            error_card = create_error_card("處理您的請求時發生錯誤。")
            return (
                error_card,
                conversation_id if conversation_id else None,
            )
