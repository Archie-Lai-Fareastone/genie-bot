"""
Connector Response 模組

此模組提供通用的 Connector 回應資料結構，供所有 connector 使用。
"""

from typing import Optional, List, Any
from dataclasses import dataclass

from utils.adaptive_card import ColumnSchema


@dataclass
class ConnectorResponse:
    """
    通用 Connector 回應資料物件
    
    此類別提供一個標準化的資料結構，用於儲存各種 connector 的回應資料。
    所有欄位都是 optional，允許不同的 connector 根據需求使用相關欄位。
    
    Attributes:
        response_text: 回應文字內容
        query_description: 查詢描述
        sql_code: SQL 程式碼
        schema_columns: 資料結構欄位定義
        data_array: 資料陣列, [[]Any]]，每個元素代表一行資料
        total_row_count: 總行數
        metadata: 額外的 metadata 資訊
        error_message: 錯誤訊息（如果有）
    """
    response_text: Optional[str] = None
    query_description: Optional[str] = None
    sql_code: Optional[str] = None
    schema_columns: Optional[List[ColumnSchema]] = None
    data_array: Optional[List[Any]] = None
    total_row_count: Optional[int] = None
    metadata: Optional[dict] = None
    error_message: Optional[str] = None
    
    def __post_init__(self):
        """初始化後處理，確保 list 類型欄位有預設值"""
        if self.schema_columns is None:
            self.schema_columns = []
        if self.data_array is None:
            self.data_array = []
        if self.metadata is None:
            self.metadata = {}
    
    def reset(self) -> None:
        """重置所有欄位為預設值"""
        self.response_text = None
        self.query_description = None
        self.sql_code = None
        self.schema_columns = []
        self.data_array = []
        self.total_row_count = None
        self.metadata = {}
        self.error_message = None
    
    def has_data(self) -> bool:
        """
        檢查是否有任何資料
        
        Returns:
            bool: 如果有任何非空資料則回傳 True
        """
        return bool(
            self.response_text or
            self.query_description or
            self.sql_code or
            self.schema_columns or
            self.data_array or
            self.total_row_count is not None or
            self.metadata
        )
    
    def has_error(self) -> bool:
        """
        檢查是否有錯誤
        
        Returns:
            bool: 如果有錯誤訊息則回傳 True
        """
        return self.error_message is not None
    
    def has_structured_data(self) -> bool:
        """
        檢查是否有結構化資料
        
        Returns:
            bool: 如果有 schema 和 data_array 則回傳 True
        """
        return bool(self.schema_columns and self.data_array)
