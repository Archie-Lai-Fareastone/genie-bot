import os
from dotenv import load_dotenv

# 載入環境變數
load_dotenv()

class DefaultConfig:
    """ Bot Configuration """

    PORT = int(os.environ.get("PORT", 3978))
    APP_ID = os.environ.get("MicrosoftAppId", "")
    APP_PASSWORD = os.environ.get("MicrosoftAppPassword", "")
    
    # Databricks Configuration
    DATABRICKS_HOST = os.environ.get("DATABRICKS_HOST", "")
    DATABRICKS_TOKEN = os.environ.get("DATABRICKS_TOKEN", "")
    DATABRICKS_SPACE_ID = os.environ.get("DATABRICKS_SPACE_ID", "")
