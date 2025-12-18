from typing import Literal, Optional
from src.core.logger_config import get_logger

logger = get_logger(__name__)

CardType = Literal["text", "chart", "table", "sql"]


def adaptive_card(
    card_type: CardType,
    content: Optional[str] = None,
    headers: Optional[list[str]] = None,
    rows: Optional[list[list[str]]] = None,
    column_widths: Optional[list[int]] = None,
) -> dict:
    """
    If user asks for a chart, a sql code snippet, or a table,
    the tool generate adaptive card to present the content.
    **IMORTANT: Return only the json content without any additional explanation when using this tool.**

    :param card_type: Type of adaptive card to generate. Options: "text", "chart", "table", "sql".
    :param content: Content to include in the adaptive card (used for "text" or "sql" card type).
    :param headers: List of column headers (used for "table" card type).
    :param rows: List of rows, where each row is a list of cell values (used for "table" card type).
    :param column_widths: Optional list of column widths (used for "table" card type). Defaults to 1 for each column.
    :return: A JSON object representing the adaptive card.
    """

    logger.info(f"建立 Adaptive card - Card Type: {card_type}")

    if card_type == "sql" or card_type == "text":
        if content is None:
            raise ValueError("參數 'content' 是 SQL card 或 Text card 的必要參數")
        return {
            "type": "AdaptiveCard",
            "version": "1.5",
            "body": [
                {
                    "type": "TextBlock",
                    "text": content,
                    "wrap": True,
                    "size": "Small",
                }
            ],
        }

    elif card_type == "table":
        if headers is None or rows is None:
            raise ValueError("參數 'headers' 和 'rows' 是 Table card 的必要參數")

        # 設定欄位寬度，預設為 1
        num_columns = len(headers)
        widths = column_widths if column_widths else [1] * num_columns

        # 建立欄位定義
        columns = [{"width": width} for width in widths]

        # 建立標題列
        header_cells = [
            {
                "type": "TableCell",
                "items": [
                    {
                        "type": "TextBlock",
                        "text": header,
                        "wrap": True,
                        "weight": "Bolder",
                    }
                ],
            }
            for header in headers
        ]

        # 建立資料列
        data_rows = []
        for row in rows:
            cells = [
                {
                    "type": "TableCell",
                    "items": [
                        {
                            "type": "TextBlock",
                            "text": str(cell),
                            "wrap": True,
                        }
                    ],
                }
                for cell in row
            ]
            data_rows.append({"type": "TableRow", "cells": cells})

        # 組合所有列
        all_rows = [{"type": "TableRow", "cells": header_cells}] + data_rows

        return {
            "type": "AdaptiveCard",
            "version": "1.5",
            "body": [
                {
                    "type": "Table",
                    "roundedCorners": True,
                    "columns": columns,
                    "rows": all_rows,
                }
            ],
        }
