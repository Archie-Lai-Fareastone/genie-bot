"""
設定模組

此模組包含專案的所有設定檔案。
"""

from src.config.genie_space_config import (
    GENIE_SPACE_CONFIG,
    GenieSpaceConfig,
    get_genie_config,
    get_all_genie_configs
)

__all__ = [
    'GENIE_SPACE_CONFIG',
    'GenieSpaceConfig',
    'get_genie_config',
    'get_all_genie_configs'
]
