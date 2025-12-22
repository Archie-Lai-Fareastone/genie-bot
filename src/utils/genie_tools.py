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
        logger.info("測試 Genie 客戶端...")
        for connection in project_client.connections.list():
            logger.info("===========")
            logger.info(connection)

        logger.info(
            f"準備初始化 {len(connection_names)} 個 Genie 連線: {connection_names}"
        )

        for connection_name in connection_names:
            try:
                logger.info(f"正在取得連線: {connection_name}")
                connection = project_client.connections.get(connection_name)
                logger.info(
                    f"連線 {connection_name} 取得成功，Target: {connection.target}"
                )

                genie_space_id = connection.metadata.get("genie_space_id")
                if not genie_space_id:
                    logger.error(f"連線 {connection_name} 缺少 genie_space_id metadata")
                    raise ValueError(f"連線 {connection_name} 缺少 genie_space_id")

                logger.info(f"正在取得 Azure 權杖...")
                token = credential.get_token(entra_id_audience_scope).token
                logger.info(f"權杖取得成功，長度: {len(token) if token else 0}")

                logger.info(f"正在建立 Databricks WorkspaceClient...")
                databricks_client = WorkspaceClient(
                    host=connection.target,
                    token=token,
                )
                logger.info(f"WorkspaceClient 建立成功")
                logger.info(f"正在取得 Genie Space ID: {genie_space_id}...")
                logger.info(f"host: {connection.target}")

                logger.info(f"正在建立 Genie 實例...")
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
