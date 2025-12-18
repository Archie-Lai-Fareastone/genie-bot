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

from src.bot import MyBot
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
bot_settings = BotFrameworkAdapterSettings(
    settings.bot["app_id"], settings.bot["app_password"]
)
ADAPTER = BotFrameworkAdapter(bot_settings)


# 錯誤處理函式
async def on_error(context: TurnContext, error: Exception):
    logger.error(f"[on_turn_error] 未處理的錯誤: {error}", exc_info=True)

    await context.send_activity("機器人遇到了錯誤或錯誤。")
    await context.send_activity("要繼續執行此機器人，請修復機器人原始程式碼。")

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
BOT = MyBot(app)


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

        async def bot_logic(turn_context: TurnContext):
            await BOT.on_turn(turn_context)

        await ADAPTER.process_activity(activity, auth_header, bot_logic)

        return JSONResponse(content={}, status_code=200)

    except Exception as e:
        logger.error(f"處理請求時發生錯誤: {str(e)}", exc_info=True)
        raise HTTPException(status_code=500, detail="Internal Server Error")


if __name__ == "__main__":
    settings = get_settings(app)
    PORT = settings.app["port"]
    HOST = settings.app["host"]
    logger.info(f"啟動 Bot 服務，監聽 {HOST}:{PORT}")
    uvicorn.run(app, host=HOST, port=PORT)
