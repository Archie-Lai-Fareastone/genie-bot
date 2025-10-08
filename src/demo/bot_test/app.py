import sys
import traceback
from datetime import datetime, timezone
import os
from aiohttp import web
from aiohttp.web import Request, Response, json_response
from botbuilder.core import TurnContext
from botbuilder.core.integration import aiohttp_error_middleware
from botbuilder.integration.aiohttp import (
    CloudAdapter,
    ConfigurationBotFrameworkAuthentication,
)
from botbuilder.schema import Activity, ActivityTypes

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../")))
from src.demo.bot_test.bot import MyBot

# 建立適配器
ADAPTER = CloudAdapter(ConfigurationBotFrameworkAuthentication(configuration={"port": 3978}))


# 錯誤處理函式
async def on_error(context: TurnContext, error: Exception):
    # 此檢查將錯誤輸出到控制台日誌
    # 注意：在生產環境中，您應該考慮將此記錄到 Azure Application Insights
    print(f"\n [on_turn_error] 未處理的錯誤: {error}", file=sys.stderr)
    traceback.print_exc()

    # 向用戶發送訊息
    await context.send_activity("機器人遇到了錯誤或錯誤。")
    await context.send_activity(
        "要繼續執行此機器人，請修復機器人原始程式碼。"
    )
    # 如果我們正在與 Bot Framework Emulator 對話，則發送追蹤活動
    if context.activity.channel_id == "emulator":
        # 建立包含錯誤物件的追蹤活動
        trace_activity = Activity(
            label="TurnError",
            name="on_turn_error Trace",
            timestamp=datetime.now(timezone.utc),
            type=ActivityTypes.trace,
            value=f"{error}",
            value_type="https://www.botframework.com/schemas/error",
        )
        # 發送追蹤活動，這將在 Bot Framework Emulator 中顯示
        await context.send_activity(trace_activity)


ADAPTER.on_turn_error = on_error

# 建立機器人
BOT = MyBot()


# 監聽 /api/messages 上的傳入請求
async def messages(req: Request) -> Response:
    # 主要機器人訊息處理程式
    if "application/json" in req.headers["Content-Type"]:
        body = await req.json()
    else:
        return Response(status=415)

    try:
        response = await ADAPTER.process(req, BOT)
        if response:
            return json_response(data=response.body, status=response.status)
        return Response(status=201)
    except Exception as e:
        print(f"處理請求時發生錯誤: {str(e)}", file=sys.stderr)
        return Response(status=500)


def init_func(argv):
    APP = web.Application(middlewares=[aiohttp_error_middleware])
    APP.router.add_post("/api/messages", messages)
    return APP


APP = web.Application(middlewares=[aiohttp_error_middleware])
APP.router.add_post("/api/messages", messages)

if __name__ == "__main__":
    try:
        web.run_app(APP, host="localhost", port=3978)
    except Exception as error:
        raise error
