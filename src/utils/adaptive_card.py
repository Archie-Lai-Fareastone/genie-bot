import os
import json
from typing import List, Any, NamedTuple, TYPE_CHECKING
from dotenv import load_dotenv

from src.utils.generate_chart_base64 import chart_to_base64
from utils.adaptive_card_formatter import format_value, convert_rows_to_columns
from utils.adaptive_card_module import (
    create_card_title,
    create_card_content,
    create_card_annotation,
    create_sql_code_block
)

if TYPE_CHECKING:
    from src.connectors.response import ConnectorResponse

class ColumnSchema(NamedTuple):
    """欄位結構定義"""
    name: str
    type: str


# 載入環境變數
load_dotenv()

MAX_CARD_ROWS = int(os.getenv("MAX_CARD_ROWS", 10))
MAX_CARD_COLUMNS = int(os.getenv("MAX_CARD_COLUMNS", 10))


def create_card_attachment(adaptive_card: dict) -> dict:
    """建立 Adaptive Card 附件"""
    return {
        "contentType": "application/vnd.microsoft.card.adaptive",
        "content": adaptive_card
    }


def create_response_card(response: 'ConnectorResponse') -> dict:
    """
    將 Genie 回傳結果轉換為 Adaptive Card
    
    Args:
        response: ConnectorResponse 物件，包含所有回應資料
    Returns:
        dict: Adaptive Card 結構
    """

    # 從 response 物件提取資料
    schema_columns = response.schema_columns or []
    data_array = response.data_array or []
    total_row_count = response.total_row_count or 0
    query_description = response.query_description or response.response_text or "沒有可用的回應內容"
    sql_code = response.sql_code or ""

    try:
        card = {
            "type": "AdaptiveCard",
            "version": "1.5",
            "body": []
        }
        
        # 加入查詢描述
        if query_description:
            card["body"].append(create_card_title("查詢說明"))
            card["body"].append(create_card_content(query_description))
        

        # 加入sql
        if sql_code:
            card["body"].append(create_card_title("SQL 語句"))
            card["body"].append(create_sql_code_block(sql_code))

        # 加入查詢結果標題
        card["body"].append(create_card_title("查詢結果"))

        # 加入統計資訊
        card["body"].append(create_card_annotation(f"共 {total_row_count} 筆資料"))
        
        # 加入表格
        if schema_columns and data_array:
            table = create_data_table(schema_columns, data_array)
            card["body"].append(table)
            
            # 如果有更多資料或欄位，顯示省略提示
            omitted_info_block = create_omitted_info(schema_columns, data_array)
            if omitted_info_block:
                card["body"].append(omitted_info_block)

        # FIXME: 加入圖表
        if data_array:
            transformed_data = convert_rows_to_columns(data_array)
            image_base64 = chart_to_base64(
                values=transformed_data[1] if len(transformed_data) > 1 else [],
                labels=transformed_data[0] if transformed_data else [],
                chart_type="vertical_bar"
            )

            if image_base64:
                card["body"].append(create_card_title("圖表"))
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
            create_card_title("錯誤", color="Attention"),
            create_card_content(error_message)
        ]
    }

    return create_card_attachment(card)


def create_text_card(message: str) -> dict:
    """建立純文字訊息的 Adaptive Card"""
    card = {
        "type": "AdaptiveCard",
        "version": "1.5",
        "body": [create_card_content(message)]
    }

    return create_card_attachment(card)


def create_menu_card():
    """建立主選單卡片"""
    
    # 讀取 Genie Space 設定檔案
    config_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)),
        "config",
        "genie_space_config.json"
    )
    
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            genie_spaces = json.load(f)
            
        # 將設定檔案轉換為選項列表
        choices = [
            {
                "title": space_info['name'],
                "value": space_id
            }
            for space_id, space_info in genie_spaces.items()
        ]
    except FileNotFoundError:
        choices = [{"title": "無法載入 Genie Space 設定", "value": ""}]
    except Exception as e:
        choices = [{"title": f"載入設定時發生錯誤: {str(e)}", "value": ""}]
    card = {
        "type": "AdaptiveCard",
        "version": "1.5",
        "body": [
            {
                "type": "Input.ChoiceSet",
                "id": "genie_space_id",
                "style": "expanded",
                "label": "選擇您要使用的 Databricks Genie Space",
                "isMultiSelect": False,
                "value": list(genie_spaces.keys())[0] if choices and choices[0].get("value") else "",
                "choices": choices
            }
        ],
        "actions": [
            {
                "type": "Action.Submit",
                "title": "OK"
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
        return create_card_annotation(
            annotation=f"... 還有 {' 和 '.join(omitted_info)}",
            horizontalAlignment="Center"
        )
    
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
            "items": [create_card_title(col.name, size="Small")]
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
                "items": [create_card_content(str(formatted_value))]
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
