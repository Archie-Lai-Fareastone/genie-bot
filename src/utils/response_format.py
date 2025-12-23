"""定義 AI Agent 回應格式的 JSON Schema"""

from azure.ai.agents.models import (
    ResponseFormatJsonSchemaType,
    ResponseFormatJsonSchema,
)


def get_genie_response_format() -> ResponseFormatJsonSchemaType:
    """取得 Genie Agent 的回應格式定義

    支援三種格式：
    1. text/sql: 純文字或 SQL 查詢回應
    2. table: 表格資料回應
    3. chart: 圖表資料回應

    Returns:
        ResponseFormatJsonSchemaType: Azure AI Agents 的回應格式物件
    """
    genie_schema = {
        "type": "object",
        "properties": {
            "card_type": {
                "type": "string",
                "description": "卡片類型，只能是以下值之一：text, sql, table, chart",
            },
            "content": {
                "type": "string",
                "description": "當 card_type 為 text 或 sql 時必須提供此欄位，包含文字內容或 SQL 查詢語法",
            },
            "headers": {
                "type": "array",
                "items": {"type": "string"},
                "description": "當 card_type 為 table 時必須提供此欄位，表格的標題列",
            },
            "rows": {
                "type": "array",
                "items": {"type": "array", "items": {"type": "string"}},
                "description": "當 card_type 為 table 時必須提供此欄位，表格的資料列，每列是字串陣列",
            },
            "labels": {
                "type": "array",
                "items": {"type": "string"},
                "description": "當 card_type 為 chart 時必須提供此欄位，圖表的 X 軸標籤",
            },
            "values": {
                "type": "array",
                "items": {"type": "string"},
                "description": "當 card_type 為 chart 時必須提供此欄位，圖表的 Y 軸數值（以字串表示）",
            },
        },
        "required": ["card_type"],
        "additionalProperties": False,
    }

    # 建立 ResponseFormatJsonSchema 物件
    json_schema = ResponseFormatJsonSchema(
        name="genie_response",
        schema=genie_schema,
        description=(
            "請直接回傳扁平的 JSON 物件，不要包裝在額外的 'type' 或 'properties' 欄位中。\n"
            "根據 card_type 的值提供對應的必要欄位：\n"
            "- 如果 card_type 是 'text' 或 'sql'：必須提供 'content' 欄位\n"
            "- 如果 card_type 是 'table'：必須提供 'headers' 和 'rows' 欄位\n"
            "- 如果 card_type 是 'chart'：必須提供 'labels' 和 'values' 欄位\n\n"
            "正確格式範例：\n"
            "{'card_type': 'text', 'content': '這是文字回應'}\n"
            "{'card_type': 'table', 'headers': ['姓名', '年齡'], 'rows': [['張三', '25'], ['李四', '30']]}\n"
            "{'card_type': 'chart', 'labels': ['一月', '二月'], 'values': ['100', '200']}"
        ),
    )

    # 建立 ResponseFormatJsonSchemaType 物件
    return ResponseFormatJsonSchemaType(json_schema=json_schema)
