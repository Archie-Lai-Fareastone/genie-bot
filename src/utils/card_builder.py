"""
處理不同類型的 agent 回應並轉換為 Adaptive Card

目前支援的卡片類型：
- 文字卡片 (text)
- SQL 指令卡片 (sql)
- 表格卡片 (table)
- 圖表卡片 (chart)
"""

from botbuilder.schema import Attachment
from src.core.logger_config import get_logger
from src.utils.chart_tool import ChartTool

logger = get_logger(__name__)


def create_text_card(content: str) -> list:
    """建立文字卡片

    Args:
        content: 文字內容

    Returns:
        Adaptive Card body 元素列表
    """
    return [{"type": "TextBlock", "text": content, "wrap": True}]


def create_sql_card(content: str) -> list:
    """建立 SQL 查詢卡片

    Args:
        content: SQL 查詢內容

    Returns:
        Adaptive Card body 元素列表
    """
    return [
        {
            "type": "TextBlock",
            "text": "SQL 指令",
            "weight": "Bolder",
            "size": "Medium",
        },
        {
            "type": "TextBlock",
            "text": content,
            "wrap": True,
            "fontType": "Monospace",
        },
    ]


def create_table_card(headers: list[str], rows: list[list[str]]) -> list:
    """建立表格卡片

    Args:
        headers: 表格標題列
        rows: 表格資料列

    Returns:
        Adaptive Card body 元素列表
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

    return [
        {
            "type": "Table",
            "columns": [{"width": "auto"} for _ in headers],
            "rows": table_rows,
        }
    ]


def create_link_card(url: str) -> list:
    """建立連結卡片

    Args:
        url: 連結 URL

    Returns:
        Adaptive Card body 元素列表
    """
    return [
        {
            "type": "TextBlock",
            "text": "點擊下方按鈕以查看詳細資訊",
            "weight": "Bolder",
            "size": "Medium",
        }
    ]


def create_chart_card(
    labels: list[str],
    values: list[str],
    chart_type: ChartTool.ChartType = "vertical_bar",
) -> list:
    """建立圖表卡片

    Args:
        labels: 圖表標籤
        values: 圖表數值
        chart_type: 圖表類型 ("pie", "donut", "horizontal_bar", "vertical_bar", "line")

    Returns:
        Adaptive Card body 元素列表
    """
    # 將 values 轉換為 float
    float_values = [float(v) for v in values]

    # 使用 chart_tools 生成圖表
    chart_data_uri = ChartTool.chart_to_base64(float_values, labels, chart_type)

    return [
        {
            "type": "TextBlock",
            "text": "圖表",
            "weight": "Bolder",
            "size": "Medium",
        },
        {
            "type": "Image",
            "url": chart_data_uri,
            "width": "360px",  # TODO: 未來可由 agent 提供更細緻化控制
        },
    ]


def convert_to_card(response_data: dict) -> Attachment:
    """將 agent 回應轉換為 Adaptive Card

    Args:
        response_data: Agent 回應資料，包含 'cards' 欄位

    Returns:
        Adaptive Card Attachment

    Raises:
        ValueError: 當卡片類型不支援時
    """
    body_elements = []
    actions = []
    logger.info(f"輸入資料: {response_data}")

    for item in response_data.get("cards", []):
        card_type = item.get("card_type")

        if card_type == "text":
            body_elements.extend(create_text_card(content=item["content"]))
        elif card_type == "sql":
            body_elements.extend(create_sql_card(content=item["content"]))
        elif card_type == "table":
            body_elements.extend(
                create_table_card(headers=item["headers"], rows=item["rows"])
            )
        elif card_type == "chart":
            body_elements.extend(
                create_chart_card(
                    labels=item["labels"],
                    values=item["values"],
                    chart_type=item.get("chart_type", "vertical_bar"),
                )
            )
        elif card_type == "link":
            body_elements.extend(create_link_card(url=item["url"]))
            actions.append(
                {
                    "type": "Action.OpenUrl",
                    "title": "在新視窗開啟連結",
                    "url": item["url"],
                }
            )
        else:
            raise ValueError(f"不支援的卡片類型: {card_type}")

    logger.info(
        f"建立包含 {len(response_data.get('cards', []))} 個元素的 Adaptive Card",
    )

    card_content = {
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": body_elements,
    }

    # 如果有 actions，添加到卡片內容中
    if actions:
        card_content["actions"] = actions

    return Attachment(
        content_type="application/vnd.microsoft.card.adaptive", content=card_content
    )
