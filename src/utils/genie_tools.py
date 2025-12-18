import json
from typing import Dict, List
from azure.identity import DefaultAzureCredential
from azure.ai.projects import AIProjectClient
from databricks.sdk import WorkspaceClient
from databricks_ai_bridge.genie import Genie

from src.core.logger_config import get_logger

logger = get_logger(__name__)


class GenieManager:
    """單例 Genie 管理器"""

    _instance: "GenieManager" = None
    _genies: Dict[str, Genie] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

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
        for connection_name in connection_names:
            connection = project_client.connections.get(connection_name)
            genie_space_id = connection.metadata["genie_space_id"]

            databricks_client = WorkspaceClient(
                host=connection.target,
                token=credential.get_token(entra_id_audience_scope).token,
            )

            self._genies[connection_name] = Genie(
                genie_space_id, client=databricks_client
            )
            logger.info(
                f"Genie 初始化完成,Connection: {connection_name}, Space ID: {genie_space_id}"
            )

        logger.info(
            f"總共初始化了 {len(self._genies)} 個 Genie 客戶端: {list(self._genies.keys())}"
        )
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
            response = self._genies[connection_name].ask_question(question)

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


# 全域實例
genie_manager = GenieManager()
