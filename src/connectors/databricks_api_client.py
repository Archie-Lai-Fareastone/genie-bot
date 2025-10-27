"""
Databricks API Client

此模組提供與 Databricks REST API 互動的客戶端類別。
"""

import requests
from typing import Optional, Dict, List

from src.utils.logger_config import get_logger

# 取得 logger 實例
logger = get_logger(__name__)


class DatabricksApiClient:
    """使用 REST API 與 Databricks 互動的客戶端"""
    
    def __init__(self, host: str, token: str):
        """
        初始化 DatabricksApiClient
        
        Args:
            host: Databricks 主機位址
            token: Databricks 存取權杖
            
        Raises:
            ValueError: 當 host 或 token 未提供時
        """
        self.host = host.rstrip('/')
        self.token = token
        
        if not self.host or not self.token:
            raise ValueError("請設定 DATABRICKS_HOST 和 DATABRICKS_TOKEN")
        
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
        
        logger.info("DatabricksApiClient 已初始化")
    
    def get_latest_history(
        self,
        catalog: str,
        schema: str,
        table: str,
        warehouse_id: str
    ) -> Dict[str, str]:
        """
        取得最新的歷史記錄
        
        Args:
            catalog: Catalog 名稱
            schema: Schema 名稱
            table: 資料表名稱
            warehouse_id: SQL Warehouse ID
            
        Returns:
            Dict[str, str]: 包含 version, timestamp, operation, userName 的字典
        """
        default_result = {
            "version": "N/A",
            "timestamp": "N/A",
            "operation": "N/A",
            "userName": "N/A"
        }
        
        try:
            url = f"{self.host}/api/2.0/sql/statements"
            payload = {
                "warehouse_id": warehouse_id,
                "statement": f"DESCRIBE HISTORY {catalog}.{schema}.{table} LIMIT 1",
                "wait_timeout": "30s"
            }
            
            logger.info(f"正在取得資料表最新歷史記錄: {catalog}.{schema}.{table}")
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            result = response.json()
            
            # 檢查查詢狀態
            if result.get('status', {}).get('state') != 'SUCCEEDED':
                logger.warning("查詢狀態不是 SUCCEEDED")
                return default_result
            
            # 解析結果
            columns = [col['name'] for col in result.get('manifest', {}).get('schema', {}).get('columns', [])]
            data_array = result.get('result', {}).get('data_array', [])
            
            if not data_array:
                return default_result
            
            # 建立記錄字典並提取所需欄位
            latest_record = dict(zip(columns, data_array[0]))
            logger.info("成功取得最新歷史記錄")
            
            return {
                key: latest_record.get(key, "N/A")
                for key in ["version", "timestamp", "operation", "userName"]
            }
                
        except requests.exceptions.RequestException as e:
            logger.error(f"取得資料表歷史記錄時發生錯誤: {str(e)}")
            return default_result
