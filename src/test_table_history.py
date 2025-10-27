"""使用 Databricks REST API 取得 Table History"""

import os
import requests
from typing import Optional, Dict, List
from dotenv import load_dotenv

load_dotenv()


class DatabricksTableHistory:
    """使用 REST API 取得 Databricks Table History"""
    
    def __init__(self):
        self.host = os.environ.get("DATABRICKS_HOST", "").rstrip('/')
        self.token = os.environ.get("DATABRICKS_TOKEN", "")
        
        if not self.host or not self.token:
            raise ValueError("請設定 DATABRICKS_HOST 和 DATABRICKS_TOKEN 環境變數")
        
        self.headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json"
        }
    
    def get_table_history(
        self,
        catalog: str,
        schema: str,
        table: str,
        warehouse_id: str,
        limit: int = 10
    ) -> Optional[List[Dict]]:
        """
        取得資料表歷史記錄
        
        Args:
            catalog: Catalog 名稱
            schema: Schema 名稱
            table: 資料表名稱
            warehouse_id: SQL Warehouse ID
            limit: 限制回傳筆數
            
        Returns:
            Optional[List[Dict]]: 歷史記錄列表
        """
        try:
            url = f"{self.host}/api/2.0/sql/statements"
            payload = {
                "warehouse_id": warehouse_id,
                "statement": f"DESCRIBE HISTORY {catalog}.{schema}.{table} LIMIT {limit}",
                "wait_timeout": "30s"
            }
            
            response = requests.post(url, headers=self.headers, json=payload)
            response.raise_for_status()
            result = response.json()
            
            if result.get('status', {}).get('state') != 'SUCCEEDED':
                return None
            
            # 解析結果
            columns = [col['name'] for col in result.get('manifest', {}).get('schema', {}).get('columns', [])]
            data_array = result.get('result', {}).get('data_array', [])
            
            return [dict(zip(columns, row)) for row in data_array]
                
        except requests.exceptions.RequestException:
            return None
    
    def get_latest_history(
        self,
        catalog: str,
        schema: str,
        table: str,
        warehouse_id: str
    ) -> Optional[Dict]:
        """取得最新的歷史記錄"""
        records = self.get_table_history(catalog, schema, table, warehouse_id, limit=1)
        return records[0] if records else None


def main():
    """主程式"""
    catalog = "develop_catalog"
    schema = "report_dw"
    table = "mds_active_mly"
    warehouse_id = os.environ.get("DATABRICKS_WAREHOUSE_ID", "")
    
    if not warehouse_id:
        print("⚠️  未設定 DATABRICKS_WAREHOUSE_ID")
        return
    
    db_api = DatabricksTableHistory()
    latest = db_api.get_latest_history(catalog, schema, table, warehouse_id)
    
    if latest:
        print(f"版本: {latest.get('version')}")
        print(f"時間: {latest.get('timestamp')}")
        print(f"操作: {latest.get('operation')}")
        print(f"使用者: {latest.get('userName', 'N/A')}")


if __name__ == "__main__":
    main()
