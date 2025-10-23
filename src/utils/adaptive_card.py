import os
from typing import List, Any, NamedTuple
from dotenv import load_dotenv

from src.utils.generate_chart_base64 import chart_to_base64

class ColumnSchema(NamedTuple):
    """欄位結構定義"""
    name: str
    type: str


# 載入環境變數
load_dotenv()

MAX_CARD_ROWS = int(os.getenv("MAX_CARD_ROWS", 10))
MAX_CARD_COLUMNS = int(os.getenv("MAX_CARD_COLUMNS", 10))


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


def create_card_attachment(adaptive_card: dict) -> dict:
    """建立 Adaptive Card 附件"""
    return {
        "contentType": "application/vnd.microsoft.card.adaptive",
        "content": adaptive_card
    }


def create_response_card(
        schema_columns: List[ColumnSchema], 
        data_array: List[List[Any]], 
        total_row_count: int,
        query_description: str = "",
        sql_code: str = ""
    ) -> dict:
    """
    將 Genie 回傳結果轉換為 Adaptive Card
    
    Args:
        schema_columns: 欄位結構資訊列表 (ColumnSchema 物件)
        data_array: 查詢結果資料陣列
        total_row_count: 總行數
        query_description: 查詢描述（可選）
        sql_code: SQL 語句（可選）
    Returns:
        dict: Adaptive Card 結構
    """

    try:
        card = {
            "type": "AdaptiveCard",
            "version": "1.5",
            "body": []
        }
        
        # 加入查詢描述
        if query_description:
            card["body"].append({
                "type": "TextBlock",
                "text": "查詢說明",
                "weight": "Bolder",
                "size": "Medium"
            })
            card["body"].append({
                "type": "TextBlock",
                "text": query_description,
                "wrap": True,
                "spacing": "Small"
            })
        

        # 加入sql
        if sql_code:
            card["body"].append({
                "type": "TextBlock",
                "text": "SQL 語句",
                "weight": "Bolder",
                "size": "Medium"
            })    
            card["body"].append({
                "type": "CodeBlock",
                "codeSnippet": sql_code,
                "language": "sql",
                "spacing": "Small"
            })

        # 加入查詢結果標題
        card["body"].append({
            "type": "TextBlock",
            "text": "查詢結果",
            "weight": "Bolder",
            "size": "Medium",
            "spacing": "Medium"
        })

        # 加入統計資訊
        card["body"].append({
            "type": "TextBlock",
            "text": f"共 {total_row_count} 筆資料",
            "size": "Small",
            "color": "Accent",
            "spacing": "Small"
        })
        
        # 加入表格
        if schema_columns and data_array:
            table = create_data_table(schema_columns, data_array)
            card["body"].append(table)
            
            # 如果有更多資料或欄位，顯示省略提示
            omitted_info_block = create_omitted_info(schema_columns, data_array)
            if omitted_info_block:
                card["body"].append(omitted_info_block)

        # 加入圖表
        if data_array and len(data_array) > 0:
            transformed_data = convert_rows_to_columns(data_array)
            title_array = transformed_data[0] if transformed_data else []
            content_array = transformed_data[1] if len(transformed_data) > 1 else []
            image_base64 = chart_to_base64(
                values=content_array,
                labels=title_array,
                chart_type="vertical_bar"
            )

            if image_base64:
                card["body"].append({
                    "type": "TextBlock",
                    "text": "圖表",
                    "weight": "Bolder",
                    "size": "Medium",
                    "spacing": "Medium"
                })
                card["body"].append({
                    "type": "Image",
                    "url": image_base64,
                    "size": "Auto",
                })
        
        return create_card_attachment(card)
    
    except Exception as e:
        return create_error_card("無法建立查詢結果卡片")


def create_error_card(error_message: str) -> dict:
    """建立錯誤訊息的 Adaptive Card"""
    card = {
        "type": "AdaptiveCard",
        "version": "1.5",
        "body": [
            {
                "type": "TextBlock",
                "text": "錯誤",
                "weight": "Bolder",
                "size": "Medium",
                "color": "Attention"
            },
            {
                "type": "TextBlock",
                "text": error_message,
                "wrap": True,
                "spacing": "Small"
            }
        ]
    }

    return create_card_attachment(card)


def create_text_card(message: str) -> dict:
    """建立純文字訊息的 Adaptive Card"""
    card = {
        "type": "AdaptiveCard",
        "version": "1.5",
        "body": [
            {
                "type": "TextBlock",
                "text": message,
                "wrap": True
            }
        ]
    }

    return create_card_attachment(card)


def create_omitted_info(schema_columns: List[ColumnSchema], data_array: List[List[Any]]) -> dict:
    """
    建立省略資訊的 TextBlock
    
    Args:
        schema_columns: 欄位結構資訊列表 (ColumnSchema 物件)
        data_array: 查詢結果資料陣列
    Returns:
        dict: Adaptive Card TextBlock 結構，如果沒有省略資訊則回傳 None
    """
    max_rows = min(MAX_CARD_ROWS, len(data_array))
    omitted_info = []
    
    if len(data_array) > max_rows:
        omitted_info.append(f"{len(data_array) - max_rows} 筆資料")
    if len(schema_columns) > MAX_CARD_COLUMNS:
        omitted_info.append(f"{len(schema_columns) - MAX_CARD_COLUMNS} 個欄位")
    
    if omitted_info:
        return {
            "type": "TextBlock",
            "text": f"... 還有 {' 和 '.join(omitted_info)}",
            "size": "Small",
            "color": "default",
            "horizontalAlignment": "Center",
            "spacing": "Small"
        }
    
    return None


def create_data_table(schema_columns: List[ColumnSchema], data_array: List[List[Any]]) -> dict:
    """
    建立 Adaptive Card 表格
    
    Args:
        schema_columns: 欄位結構資訊列表 (ColumnSchema 物件)
        data_array: 查詢結果資料陣列
    Returns:
        dict: Adaptive Card 表格結構
    """
    # 限制顯示的欄位數量
    display_columns = schema_columns[:MAX_CARD_COLUMNS]
    max_rows = min(MAX_CARD_ROWS, len(data_array))
    
    # 建立欄位定義
    table_columns = []
    for _ in display_columns:
        table_columns.append({"width": 1})
    
    # 建立表格行
    table_rows = []
    
    # 標題行
    header_cells = []
    for col in display_columns:
        header_cells.append({
            "type": "TableCell",
            "items": [
                {
                    "type": "TextBlock",
                    "text": col.name,
                    "wrap": True,
                    "weight": "Bolder",
                    "size": "Small"
                }
            ]
        })
    
    table_rows.append({
        "type": "TableRow",
        "cells": header_cells,
        "style": "accent"
    })
    
    # 資料行
    for i in range(max_rows):
        row = data_array[i]
        data_cells = []
        
        for j, (value, col_info) in enumerate(zip(row[:MAX_CARD_COLUMNS], display_columns)):
            # 格式化數值
            formatted_value = format_value(value, col_info.type)
            data_cells.append({
                "type": "TableCell",
                "style": "emphasis",
                "items": [
                    {
                        "type": "TextBlock",
                        "text": str(formatted_value),
                        "wrap": True,
                        "size": "Small"
                    }
                ]
            })
        
        table_rows.append({
            "type": "TableRow",
            "cells": data_cells
        })
    
    # 建立表格
    table = {
        "type": "Table",
        "gridStyle": "accent",
        "showGridLines": True,
        "columns": table_columns,
        "rows": table_rows
    }
    
    return table


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