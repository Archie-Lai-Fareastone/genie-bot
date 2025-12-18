"""
Settings Module

集中管理所有應用程式配置,根據環境載入不同來源的配置
"""

import os
from typing import Dict, Any
from dotenv import load_dotenv
from fastapi import FastAPI


class Settings:
    """
    應用程式配置類別

    根據環境(development/production)載入不同來源的配置
    - development: 從 .env 檔案載入
    - production: 從雲端 Secrets 管理服務載入
    """

    def __init__(self):
        self.app_env = os.getenv("APP_ENV", "development")

        # 應用程式配置
        self.app: Dict[str, Any] = {}

        # Microsoft Bot Framework 配置
        self.bot: Dict[str, Any] = {}

        # Azure AI Foundry 配置
        self.azure_foundry: Dict[str, Any] = {}

        # Databricks 配置
        self.databricks: Dict[str, Any] = {}

        # 載入所有配置
        self._load_config()

    def _load_config(self):
        """載入所有配置"""
        if self.app_env == "development":
            self._load_from_env()
        elif self.app_env == "production":
            # TODO: 從雲端 Secrets 管理服務載入配置
            self._load_from_env()
        else:
            raise ValueError(f"未知的環境: {self.app_env}")

    def _load_from_env(self):
        """從 .env 檔案載入配置(開發環境)"""
        load_dotenv()

        # 應用程式配置
        self.app = {
            "port": int(os.getenv("PORT", "3978")),
            "host": os.getenv("HOST", "localhost"),
            "release_version": os.getenv("APP_RELEASE_VERSION", "1.0.0"),
        }

        # Microsoft Bot Framework 配置
        self.bot = {
            "app_id": os.getenv("MicrosoftAppId", ""),
            "app_password": os.getenv("MicrosoftAppPassword", ""),
        }

        # Azure AI Foundry 配置
        self.azure_foundry = {
            "project_endpoint": os.getenv("AZURE_FOUNDRY_PROJECT_ENDPOINT"),
            "agent_id": os.getenv("AZURE_AI_AGENT_ID"),
            "connection_names": [
                "Active_dataset_Rag_bst",
                "Finance_dataset_Rag_bst",
            ],
        }

        # Databricks 配置
        self.databricks = {
            "entra_id_audience_scope": os.getenv("DATABRICKS_ENTRA_ID_AUDIENCE_SCOPE"),
        }

    def set_config(self, category: str, key: str, value: Any) -> None:
        """
        動態設定配置項目

        Args:
            category: 配置類別 ('app', 'bot', 'azure_foundry', 'databricks')
            key: 配置項目的鍵
            value: 配置項目的值

        Raises:
            ValueError: 當配置類別不存在時拋出

        Example:
            >>> settings = Settings()
            >>> settings.set_config("app", "port", 8080)
            >>> settings.set_config("azure_foundry", "agent_id", "new-agent-id")
        """
        if not hasattr(self, category):
            raise ValueError(f"不支援的配置類別: {category}")

        config_dict = getattr(self, category)
        config_dict[key] = value

    def get_config(self, category: str, key: str, default: Any = None) -> Any:
        """
        取得配置項目的值

        Args:
            category: 配置類別 ('app', 'bot', 'azure_foundry', 'databricks')
            key: 配置項目的鍵
            default: 當鍵不存在時的預設值

        Returns:
            配置項目的值,若不存在則返回預設值

        Example:
            >>> settings = Settings()
            >>> port = settings.get_config("app", "port", 3978)
        """
        if not hasattr(self, category):
            return default

        config_dict = getattr(self, category)
        return config_dict.get(key, default)


def init_settings(app: FastAPI):
    """
    初始化應用程式配置並存入 app.state

    在 FastAPI 應用程式啟動時呼叫此函式,將配置載入至 app.state
    以便在整個應用程式生命週期中存取

    Args:
        app: FastAPI 應用程式實例

    Example:
        >>> from fastapi import FastAPI
        >>> app = FastAPI()
        >>> init_settings(app)
        >>> # 現在可以透過 app.state.settings 存取配置
    """
    settings = Settings()
    app.state.settings = settings


def get_settings(app: FastAPI) -> Settings:
    """
    從 FastAPI app.state 取得配置

    Args:
        app: FastAPI 應用程式實例

    Returns:
        Settings: 應用程式配置物件

    Example:
        >>> from fastapi import Request
        >>> @app.get("/")
        >>> async def handler(request: Request):
        >>>     settings = get_settings(request.app)
        >>>     return {"version": settings.app["release_version"]}
    """
    return app.state.settings
