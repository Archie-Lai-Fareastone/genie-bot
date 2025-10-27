"""
Genie Space 設定檔

此檔案包含所有 Genie Space 的設定資訊，包括名稱和描述。
每個 Genie Space 由其唯一的 ID 作為鍵值。
"""

from typing import Dict, TypedDict


class GenieSpaceConfig(TypedDict):
    """Genie Space 設定的型別定義"""
    name: str
    description: str


# Genie Space 設定字典
GENIE_SPACE_CONFIG: Dict[str, GenieSpaceConfig] = {
    "01eff456fa5a179d83b0b5dadc7b2a52": {
        "name": "develop_genie",
        "description": "develop catalog 相關資料集查詢專家。專門處理開發目錄中的資料集查詢、資料集結構和內容分析、資料品質檢查、生成資料集相關報表和洞察、回答與開發目錄相關的技術問題。"
    },
    "01f098e4d26f1ecd9ad7342aace672cc": {
        "name": "active_dataset_genie",
        "description": "查詢活躍資料集的專業助理。可以分析資料集使用情況和活躍度、提供資料品質洞察、生成資料集相關報表、回答資料集結構和內容問題。"
    },
    "01f08d4d6e4d126e8dd31d39018a3009": {
        "name": "location_code_genie",
        "description": "位置程式碼查詢專家。專門處理地理位置程式碼查詢和驗證、位置層級映射和轉換、區域分析和地理資料洞察、位置相關的商業智慧查詢。"
    }
}


def get_genie_config(genie_space_id: str) -> GenieSpaceConfig | None:
    """
    根據 Genie Space ID 取得設定
    
    Args:
        genie_space_id: Genie Space 的唯一識別碼
        
    Returns:
        GenieSpaceConfig 或 None (如果找不到對應的設定)
    """
    return GENIE_SPACE_CONFIG.get(genie_space_id)


def get_all_genie_configs() -> Dict[str, GenieSpaceConfig]:
    """
    取得所有 Genie Space 設定
    
    Returns:
        包含所有 Genie Space 設定的字典
    """
    return GENIE_SPACE_CONFIG
