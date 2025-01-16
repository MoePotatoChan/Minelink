import logging
import json
import websocket
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
import threading
# 日志设置
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# WebSocket 服务器地址
WEBSOCKET_SERVER = 'ws://localhost:23089'

# Telegram Bot Token
BOT_TOKEN = ''

# 发送 WebSocket 消息并获取响应

def send_websocket_command(command):
    def on_message(ws, message):
        nonlocal response
        data = json.loads(message)
        response = data.get("response", "No response from server.")
        ws.close()  # 收到消息后关闭连接

    def on_error(ws, error):
        nonlocal response
        response = f"WebSocket error: {error}"
        ws.close()

    def on_close(ws, close_status_code, close_msg):
        logger.info("WebSocket connection closed.")

    def on_open(ws):
        ws.send(command)

    response = "No response from server."
    ws = websocket.WebSocketApp(WEBSOCKET_SERVER,
                                on_message=on_message,
                                on_error=on_error,
                                on_close=on_close)
    ws.on_open = on_open

    # 使用线程运行 WebSocket，避免阻塞主线程
    ws_thread = threading.Thread(target=ws.run_forever)
    ws_thread.start()
    ws_thread.join(timeout=10)  # 设置超时时间为 10 秒

    if ws_thread.is_alive():
        ws.close()
        response = "WebSocket request timed out."

    return response

#预配白名单
ADMIN_IDS = []  # 把管理员的Telegram用户ID填进去，比如 [123456789, 987654321]

# 判断admin
async def is_admin(update: Update, context: ContextTypes.DEFAULT_TYPE) -> bool:
    if update.effective_user.id in ADMIN_IDS:
        return True
    
    if update.effective_chat.type in ['group', 'supergroup']:
        chat_member = await context.bot.get_chat_member(
            chat_id=update.effective_chat.id,
            user_id=update.effective_user.id
        )
        return chat_member.status in ['administrator', 'creator']
    
    return False

def admin_required(func):
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE):
        if await is_admin(update, context):
            return await func(update, context)
        else:
            await update.message.reply_text("抱歉，此命令仅限群管理员或白名单用户使用。")
    return wrapper

# /start 命令
@admin_required
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text("欢迎使用 Minecraft 服务器控制工具！")

# /execute 命令：执行自定义命令
@admin_required
async def execute(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    command = ' '.join(context.args)
    if not command:
        await update.message.reply_text("请提供要执行的命令。")
        return

    response = send_websocket_command(command)
    await update.message.reply_text(response)

# /load 命令：查询服务器负载信息
async def load(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    response = send_websocket_command("load")
    await update.message.reply_text(response)

# /log 命令：获取日志
async def log(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    response = send_websocket_command("log")
    await update.message.reply_text(response)

# 主函数

def main() -> None:
    # 初始化 Telegram Bot
    application = Application.builder().token(BOT_TOKEN).build()

    # 注册命令
    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("execute", execute))
    application.add_handler(CommandHandler("load", load))
    application.add_handler(CommandHandler("log", log))

    # 启动 Bot
    application.run_polling()

if __name__ == '__main__':
    main()