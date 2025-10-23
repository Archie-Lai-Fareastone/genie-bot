import sys
import traceback
from datetime import datetime, timezone
import os
import uvicorn
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from botbuilder.core import TurnContext, BotFrameworkAdapter, BotFrameworkAdapterSettings
from botbuilder.schema import Activity, ActivityTypes

from src.bot import MyBot


# 建立適配器設定
APP_ID = os.environ.get("MicrosoftAppId", "")
APP_PASSWORD = os.environ.get("MicrosoftAppPassword", "")
SETTINGS = BotFrameworkAdapterSettings(APP_ID, APP_PASSWORD)

# 建立適配器
ADAPTER = BotFrameworkAdapter(SETTINGS)

# 建立 FastAPI 應用程式
app = FastAPI()

# 錯誤處理函式
async def on_error(context: TurnContext, error: Exception):
    print(f"\n [on_turn_error] 未處理的錯誤: {error}", file=sys.stderr)
    traceback.print_exc()

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
BOT = MyBot()

# 主要訊息處理端點
@app.post("/api/messages")
async def messages(request: Request):
    try:
        # 檢查內容類型
        content_type = request.headers.get("content-type", "")
        if "application/json" not in content_type:
            raise HTTPException(status_code=415, detail="Unsupported Media Type")
        
        # 取得請求內容
        body = await request.json()
        
        # 取得授權標頭
        auth_header = request.headers.get("authorization", "")
        
        # 建立 Activity 物件
        activity = Activity().deserialize(body)
        
        # 建立回調函數來處理 turn context
        async def bot_logic(turn_context: TurnContext):
            print(f"DEBUG: bot_logic 被呼叫，活動類型: {turn_context.activity.type}")
            print(f"DEBUG: 活動文字: {turn_context.activity.text}")
            await BOT.on_turn(turn_context)
        
        # 處理機器人請求
        await ADAPTER.process_activity(activity, auth_header, bot_logic)
        
        return JSONResponse(content={}, status_code=200)
        
    except Exception as e:
        print(f"處理請求時發生錯誤: {str(e)}", file=sys.stderr)
        traceback.print_exc()
        raise HTTPException(status_code=500, detail="Internal Server Error")

if __name__ == "__main__":
    PORT = int(os.environ.get("PORT", 3978))
    uvicorn.run(app, host="localhost", port=PORT)
