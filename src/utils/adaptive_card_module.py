"""
建立 Adaptive Card 的模組
"""

def create_card_title(title: str, color: str = "Default", size: str = "Medium") -> dict:
    """建立卡片標題"""
    return {
        "type": "TextBlock",
        "text": title,
        "weight": "Bolder",
        "size": size,
        "wrap": True,
        "spacing": "Medium",
        "color": color
    }

def create_card_content(content: str) -> dict:
    """建立卡片內容"""
    return {
        "type": "TextBlock",
        "text": content,
        "wrap": True,
        "spacing": "Small"
    }

def create_card_annotation(annotation: str, horizontalAlignment: str = "left") -> dict:
    """建立卡片註解"""
    return {
            "type": "TextBlock",
            "text": annotation,
            "size": "Small",
            "color": "Default",
            "spacing": "Small",
            "horizontalAlignment": horizontalAlignment
    }

def create_sql_code_block(sql: str) -> dict:
    """建立 SQL 查詢的程式碼區塊"""
    return {
        "type": "CodeBlock",
        "codeSnippet": sql,
        "language": "sql",
        "spacing": "Small"
    }