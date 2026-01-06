"""處理不同類型的 agent 回應並轉換為 Adaptive Card"""

from botbuilder.schema import Attachment
from src.core.logger_config import get_logger
from src.utils.chart_tool import ChartTool
from typing import List, Dict, Any

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


def create_chart_card(
    labels: list[str],
    values: list[str],
    chart_type: ChartTool.ChartType = "vertical_bar",
) -> dict:
    """建立圖表卡片

    Args:
        labels: 圖表標籤
        values: 圖表數值
        chart_type: 圖表類型 ("pie", "donut", "horizontal_bar", "vertical_bar", "line")

    Returns:
        Adaptive Card JSON
    """
    # 將 values 轉換為 float
    float_values = [float(v) for v in values]

    # 使用 chart_tools 生成圖表
    chart_data_uri = ChartTool.chart_to_base64(float_values, labels, chart_type)

    return {
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": [
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
        ],
    }


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
    logger.info(f"輸入資料: {response_data}")

    for item in response_data.get("cards", []):
        card_type = item.get("card_type")

        if card_type == "text":
            card = create_text_card(content=item["content"])
        elif card_type == "sql":
            card = create_sql_card(content=item["content"])
        elif card_type == "table":
            card = create_table_card(headers=item["headers"], rows=item["rows"])
        elif card_type == "chart":
            card = create_chart_card(
                labels=item["labels"],
                values=item["values"],
                chart_type=item.get("chart_type", "vertical_bar"),
            )
        else:
            raise ValueError(f"不支援的卡片類型: {card_type}")

        body_elements.extend(card["body"])

    logger.info(
        f"建立包含 {len(response_data.get('cards', []))} 個元素的 Adaptive Card",
    )

    card_content = {
        "type": "AdaptiveCard",
        "version": "1.4",
        "body": body_elements,
    }

    return Attachment(
        content_type="application/vnd.microsoft.card.adaptive", content=card_content
    )


def create_file_upload_confirmation_card(files: List[Dict[str, Any]]) -> Attachment:
    """
    建立檔案上傳確認 Adaptive Card

    Args:
        files: 檔案清單，每個檔案應包含:
            - name: 檔案名稱
            - size: 檔案大小（位元組）
            - content_type: MIME 類型（選填）

    Returns:
        Adaptive Card Attachment
    """
    # 建立檔案清單元素
    file_items = []

    # 標題
    file_items.append(
        {
            "type": "TextBlock",
            "text": "✅ 檔案上傳成功",
            "weight": "Bolder",
            "size": "Large",
            "color": "Good",
        }
    )

    file_items.append(
        {
            "type": "TextBlock",
            "text": f"已成功接收 {len(files)} 個檔案：",
            "wrap": True,
            "spacing": "Medium",
        }
    )

    # 為每個檔案建立一個 FactSet
    for idx, file_info in enumerate(files, 1):
        name = file_info.get("name", "未知檔案")
        size = file_info.get("size", 0)
        content_type = file_info.get("content_type", "未知類型")

        # 格式化檔案大小
        size_str = format_file_size(size)

        # 檔案資訊區塊
        file_items.append(
            {
                "type": "Container",
                "spacing": "Medium",
                "separator": True if idx > 1 else False,
                "items": [
                    {
                        "type": "TextBlock",
                        "text": f"📄 檔案 {idx}",
                        "weight": "Bolder",
                        "size": "Medium",
                    },
                    {
                        "type": "FactSet",
                        "facts": [
                            {"title": "檔案名稱:", "value": name},
                            {"title": "檔案大小:", "value": size_str},
                            {"title": "檔案類型:", "value": content_type},
                        ],
                    },
                ],
            }
        )

    # 建立完整卡片
    card_content = {"type": "AdaptiveCard", "version": "1.4", "body": file_items}

    logger.info(f"建立檔案上傳確認卡片，包含 {len(files)} 個檔案")

    return Attachment(
        content_type="application/vnd.microsoft.card.adaptive", content=card_content
    )


def format_file_size(size_bytes: int) -> str:
    """
    格式化檔案大小為人類可讀格式

    Args:
        size_bytes: 檔案大小（位元組）

    Returns:
        格式化的檔案大小字串
    """
    # 處理無效或未知的檔案大小
    if not isinstance(size_bytes, (int, float)) or size_bytes <= 0:
        return "未知大小"

    if size_bytes < 1024:
        return f"{size_bytes} B"
    elif size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.2f} KB"
    elif size_bytes < 1024 * 1024 * 1024:
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    else:
        return f"{size_bytes / (1024 * 1024 * 1024):.2f} GB"
