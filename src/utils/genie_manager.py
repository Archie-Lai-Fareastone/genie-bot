"""
提供 Foundry Agent 使用的 Genie 工具集管理功能
"""

import json
from typing import Dict, List
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from databricks.sdk import WorkspaceClient
from databricks_ai_bridge.genie import Genie

from src.core.logger_config import get_logger

logger = get_logger(__name__)


class GenieManager:
    """
    Genie 管理器

    由呼叫端（例如 Bot 實例）持有此管理器，將狀態限制在該 Bot 生命週期內，
    避免使用全域狀態造成難以追蹤的副作用。
    """

    def __init__(self):
        self._genies: Dict[str, Genie] = {}
        self._credential: DefaultAzureCredential | None = None
        self._entra_id_audience_scope: str | None = None
        self._connections: Dict[str, dict] = {}

    def initialize(
        self,
        project_client: AIProjectClient,
        credential: DefaultAzureCredential,
        connection_names: List[str],
        entra_id_audience_scope: str,
    ) -> Dict[str, Genie]:
        """初始化多個 Genie 客戶端

        Args:
            project_client: Azure AI Project Client
            credential: Azure 認證
            connection_names: Genie 連線名稱列表
            entra_id_audience_scope: Entra ID 受眾範圍

        Returns:
            字典,鍵為連線名稱,值為 Genie 物件
        """
        logger.info(
            f"準備初始化 {len(connection_names)} 個 Genie 連線: {connection_names}"
        )

        self._credential = credential
        self._entra_id_audience_scope = entra_id_audience_scope

        for connection_name in connection_names:
            try:
                logger.info(f"正在取得連線: {connection_name}")
                connection = project_client.connections.get(connection_name)
                genie_space_id = connection.metadata.get("genie_space_id")
                if not genie_space_id:
                    logger.error(f"連線 {connection_name} 缺少 genie_space_id metadata")
                    raise ValueError(f"連線 {connection_name} 缺少 genie_space_id")

                # 保存連線資訊，供token過期時重建使用
                self._connections[connection_name] = {
                    "target": connection.target,
                    "genie_space_id": genie_space_id,
                }

                token = credential.get_token(entra_id_audience_scope).token
                databricks_client = WorkspaceClient(
                    host=connection.target,
                    token=token,
                )
                self._genies[connection_name] = Genie(
                    genie_space_id, client=databricks_client
                )
                logger.info(
                    f"Genie 初始化完成,Connection: {connection_name}, Space ID: {genie_space_id}"
                )

            except Exception as e:
                logger.error(
                    f"初始化 Genie 連線 {connection_name} 失敗: {e}", exc_info=True
                )
                # 繼續處理其他連線，而不是完全失敗
                continue

        if not self._genies:
            error_msg = "所有 Genie 連線初始化失敗"
            logger.error(error_msg)
            raise RuntimeError(error_msg)

        return self._genies

    def ask_genie(self, connection_name: str, question: str) -> str:
        """向指定的 Genie 提問

        Args:
            connection_name: Genie 連線名稱
            question: 要詢問的問題

        Returns:
            JSON 格式的回應，包含 connection_name, query, result, description 或 error
        """
        try:
            if connection_name not in self._genies:
                available = ", ".join(self._genies.keys())
                logger.warning(
                    f"無效的 connection_name: {connection_name}。可用選項: {available}"
                )
                return json.dumps(
                    {
                        "error": f"無效的 connection_name: {connection_name}。可用的選項: {available}"
                    }
                )

            logger.info(f"使用 Genie [{connection_name}] 處理問題: {question}")

            try:
                response = self._genies[connection_name].ask_question(question)
            except Exception as e:
                # Token過期時自動重建客戶端並重試
                if "401" in str(e) or "Token is expired" in str(e):
                    logger.warning(f"Token已過期,重新建立客戶端: {connection_name}")
                    conn_info = self._connections[connection_name]
                    if not self._credential or not self._entra_id_audience_scope:
                        raise RuntimeError(
                            "GenieManager 尚未 initialize，無法重新取得 token"
                        )

                    token = self._credential.get_token(
                        self._entra_id_audience_scope
                    ).token
                    self._genies[connection_name] = Genie(
                        conn_info["genie_space_id"],
                        client=WorkspaceClient(host=conn_info["target"], token=token),
                    )
                    response = self._genies[connection_name].ask_question(question)
                else:
                    raise e

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
