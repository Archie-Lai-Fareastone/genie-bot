"""
Connectors 模組

此模組提供各種資料來源的連接器。
"""

from src.connectors.response import ConnectorResponse
from src.connectors.genie_connector import GenieConnector

__all__ = [
    'ConnectorResponse',
    'GenieConnector',
]
