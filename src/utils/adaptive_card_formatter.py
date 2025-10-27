"""
資料格式化與轉換工具模組

提供資料格式化、型別轉換和陣列轉置等通用工具函式
"""

from typing import List, Any


def format_value(value: Any, column_type: str) -> str:
    """
    根據欄位類型格式化數值（大小寫不敏感）
    
    Args:
        value: 要格式化的值
        column_type: 欄位型別字串（支援大小寫不敏感）
    Returns:
        str: 格式化後的字串
    
    支援的型別：
        - 浮點數：DECIMAL, DOUBLE, FLOAT, REAL, NUMERIC
        - 整數：INT, BIGINT, LONG, INTEGER, SMALLINT, TINYINT
        - 其他：以字串形式回傳
    """
    if value is None:
        return "NULL"
    
    try:
        column_type_upper = column_type.upper()
        
        # 浮點數型別
        if column_type_upper in ["DECIMAL", "DOUBLE", "FLOAT", "REAL", "NUMERIC"]:
            return f"{float(value):,.2f}"
        # 整數型別
        elif column_type_upper in ["INT", "BIGINT", "LONG", "INTEGER", "SMALLINT", "TINYINT"]:
            return f"{int(value):,}"
        # 其他型別（包含字串、日期等）
        else:
            return str(value)
    except (ValueError, TypeError):
        return str(value)
    

def convert_rows_to_columns(data_array: List[List[Any]]) -> List[List[Any]]:
    """
    將二維陣列（列為主）轉換為以欄位為主的一維陣列列表
    
    Args:
        data_array: 查詢結果資料陣列 [[row1_col1, row1_col2, ...], [row2_col1, row2_col2, ...], ...]
    Returns:
        List[List[Any]]: 以欄位為主的陣列列表 [[row1_col1, row2_col1, ...], [row1_col2, row2_col2, ...], ...]
    
    Example:
        >>> data = [[1, 'Alice'], [2, 'Bob'], [3, 'Charlie']]
        >>> convert_rows_to_columns(data)
        [[1, 2, 3], ['Alice', 'Bob', 'Charlie']]
    """
    if not data_array or not data_array[0]:
        return []
    
    # 使用 zip 轉置矩陣
    return [list(col) for col in zip(*data_array)]
