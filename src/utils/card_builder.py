"""處理不同類型的 Genie 回應並轉換為 Adaptive Card"""

from botbuilder.schema import Attachment
from src.core.logger_config import get_logger

logger = get_logger(__name__)


def create_text_card(content: str) -> dict:
    """建立文字卡片

    Args:
        content: 文字內容

    Returns:
        Adaptive Card JSON
    """
    return {
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [{"type": "TextBlock", "text": content, "wrap": True}],
    }


def create_sql_card(content: str) -> dict:
    """建立 SQL 查詢卡片

    Args:
        content: SQL 查詢內容

    Returns:
        Adaptive Card JSON
    """
    return {
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
            {
                "type": "TextBlock",
                "text": "SQL 查詢",
                "weight": "Bolder",
                "size": "Medium",
            },
            {
                "type": "TextBlock",
                "text": content,
                "wrap": True,
                "fontType": "Monospace",
            },
        ],
    }


def create_table_card(headers: list[str], rows: list[list[str]]) -> dict:
    """建立表格卡片

    Args:
        headers: 表格標題列
        rows: 表格資料列

    Returns:
        Adaptive Card JSON
    """
    # 建立表格列
    table_rows = []

    # 標題列
    header_row = {
        "type": "TableRow",
        "cells": [
            {
                "type": "TableCell",
                "items": [{"type": "TextBlock", "text": header, "weight": "Bolder"}],
            }
            for header in headers
        ],
    }
    table_rows.append(header_row)

    # 資料列
    for row in rows:
        data_row = {
            "type": "TableRow",
            "cells": [
                {
                    "type": "TableCell",
                    "items": [{"type": "TextBlock", "text": str(cell)}],
                }
                for cell in row
            ],
        }
        table_rows.append(data_row)

    return {
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
            {
                "type": "Table",
                "columns": [{"width": "auto"} for _ in headers],
                "rows": table_rows,
            }
        ],
    }


def create_chart_card(labels: list[str], values: list[str]) -> dict:
    """建立圖表卡片

    Args:
        labels: 圖表標籤
        values: 圖表數值

    Returns:
        Adaptive Card JSON
    """
    facts = [{"title": label, "value": value} for label, value in zip(labels, values)]

    return {
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
            {
                "type": "TextBlock",
                "text": "資料視覺化",
                "weight": "Bolder",
                "size": "Medium",
            },
            {"type": "FactSet", "facts": facts},
        ],
    }


def convert_to_adaptive_card(response_data: dict) -> Attachment:
    """將 Genie 回應轉換為 Adaptive Card

    Args:
        response_data: Genie 回應資料

    Returns:
        Adaptive Card Attachment

    Raises:
        ValueError: 當卡片類型不支援時
    """
    card_type = response_data.get("card_type")

    if card_type == "text":
        card_content = create_text_card(response_data["content"])
    elif card_type == "sql":
        card_content = create_sql_card(response_data["content"])
    elif card_type == "table":
        card_content = create_table_card(
            response_data["headers"], response_data["rows"]
        )
    elif card_type == "chart":
        card_content = create_chart_card(
            response_data["labels"], response_data["values"]
        )
    else:
        raise ValueError(f"不支援的卡片類型: {card_type}")

    logger.info(f"建立 {card_type} 類型的 Adaptive Card")

    return Attachment(
        content_type="application/vnd.microsoft.card.adaptive", content=card_content
    )
