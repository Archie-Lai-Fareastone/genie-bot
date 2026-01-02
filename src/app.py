from datetime import datetime, timezone
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from botbuilder.core import (
    TurnContext,
    BotFrameworkAdapter,
    BotFrameworkAdapterSettings,
)
from botbuilder.schema import Activity, ActivityTypes
from botbuilder.integration.aiohttp import (
    CloudAdapter,
    ConfigurationBotFrameworkAuthentication,
)

from src.bot.foundry_bot import FoundryBot
from src.bot.genie_bot import GenieBot
from src.core.logger_config import setup_logging, get_logger
from src.core.settings import init_settings, get_settings

# 初始化日誌系統
setup_logging()
logger = get_logger(__name__)

# 建立 FastAPI 應用程式
app = FastAPI()

# 初始化設定
init_settings(app)
settings = get_settings(app)

# 建立適配器
if settings.bot["app_id"] != "" and settings.bot["app_password"] != "":
    # Production: Use CloudAdapter
    class BotConfig:
        APP_ID = settings.bot["app_id"]
        APP_PASSWORD = settings.bot["app_password"]
        APP_TYPE = settings.bot["app_type"]
        APP_TENANTID = settings.bot["app_tenantid"]

    ADAPTER = CloudAdapter(ConfigurationBotFrameworkAuthentication(BotConfig()))
    logger.info("CloudAdapter 已建立 (生產環境)")
else:
    # Local testing: Use BotFrameworkAdapter with empty credentials
    SETTINGS = BotFrameworkAdapterSettings("", "")
    ADAPTER = BotFrameworkAdapter(SETTINGS)
    logger.info("BotFrameworkAdapter 已建立 (本地開發)")


# 錯誤處理函式
async def on_error(context: TurnContext, error: Exception):
    logger.error(f"[on_turn_error] 未處理的錯誤: {error}", exc_info=True)

    await context.send_activity("機器人遇到了錯誤，請稍後再試。")

    if context.activity.channel_id == "emulator":
        trace_activity = Activity(
            label="TurnError",
            name="on_turn_error Trace",
            timestamp=datetime.now(timezone.utc),
            type=ActivityTypes.trace,
            value=f"{error}",
            value_type="https://www.botframework.com/schemas/error",
        )
        await context.send_activity(trace_activity)


ADAPTER.on_turn_error = on_error

# 建立機器人
if settings.app["bot_mode"] == "foundry":
    BOT = FoundryBot(app)
    logger.info("FoundryBot 實例已建立")
elif settings.app["bot_mode"] == "genie":
    BOT = GenieBot(app)
    logger.info("GenieBot 實例已建立")
else:
    logger.error(f"未知的 BOT_MODE: {settings.app['bot_mode']}")
    raise ValueError(f"未知的 BOT_MODE: {settings.app['bot_mode']}")


# 啟動事件 - 啟動背景清理任務
@app.on_event("startup")
async def startup_event():
    BOT.start_cleanup_task()
    logger.info("應用啟動完成，清理任務已啟動")


# 主要訊息處理端點
@app.post("/api/messages")
async def messages(request: Request):
    try:
        content_type = request.headers.get("content-type", "")
        if "application/json" not in content_type:
            raise HTTPException(status_code=415, detail="Unsupported Media Type")

        body = await request.json()
        auth_header = request.headers.get("authorization", "")

        activity = Activity().deserialize(body)

        # 根據適配器類型使用不同的處理方式
        if hasattr(ADAPTER, "process"):
            # CloudAdapter - 直接使用 process 方法
            response = await ADAPTER.process(request, BOT)
            if response:
                return JSONResponse(content=response.body, status_code=response.status)
            return JSONResponse(content={}, status_code=201)
        else:
            # BotFrameworkAdapter - 使用 process_activity
            response = await ADAPTER.process_activity(
                activity, auth_header, BOT.on_turn
            )
            if response:
                return JSONResponse(content=response.body, status_code=response.status)
            return JSONResponse(content={}, status_code=201)

    except Exception as e:
        logger.error(f"處理請求時發生錯誤: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")


if __name__ == "__main__":
    settings = get_settings(app)
    PORT = settings.app["port"]
    HOST = settings.app["host"]
    logger.info(f"啟動 Bot 服務，監聽 {HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT)
