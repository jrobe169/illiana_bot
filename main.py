import logging
import os
import asyncio
from datetime import datetime, timedelta
from telegram import Update, ChatMember
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ChatMemberHandler
)
from flask import Flask
from threading import Thread

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Telegram Bot Token and Group
TOKEN = os.getenv("BOT_TOKEN", "your-telegram-bot-token")
GROUP_ID = -1002116956436  # Replace with your group ID

# Track user joins
joined_users = {}
AFFIRM_KEYWORDS = ["i affirm", "affirm", "i agree", "👍"]

# Flask app
flask_app = Flask(__name__)
@flask_app.route("/")
def home():
    return "Bot is running!"

# Message Handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != GROUP_ID:
        return
    message_text = update.message.text.lower().strip()
    user_id = update.effective_user.id
    if any(kw in message_text for kw in AFFIRM_KEYWORDS):
        username = update.effective_user.username or update.effective_user.full_name
        await update.message.reply_text(f"🕊️ Welcome {username}! Your affirmation has been recorded.")
        joined_users.pop(user_id, None)
        logger.info(f"{username} affirmed.")

# Member Join Handler
async def handle_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_member: ChatMember = update.chat_member
    if chat_member.new_chat_member.status == "member":
        user_id = chat_member.from_user.id
        username = chat_member.from_user.username or chat_member.from_user.full_name
        joined_users[user_id] = datetime.now()
        await context.bot.send_message(
            chat_id=GROUP_ID,
            text=f"👋 Welcome {username}! Please affirm by typing 'I Affirm', 'Affirm', 'I Agree' or sending 👍 within 10 minutes."
        )
        logger.info(f"{username} joined.")

# Scheduled Removal Task
async def check_unaffirmed_users(app: Application):
    while True:
        now = datetime.now()
        for user_id, joined_at in list(joined_users.items()):
            if now - joined_at > timedelta(minutes=10):
                try:
                    await app.bot.ban_chat_member(chat_id=GROUP_ID, user_id=user_id)
                    await app.bot.unban_chat_member(chat_id=GROUP_ID, user_id=user_id)
                    logger.info(f"User {user_id} removed for not affirming.")
                    del joined_users[user_id]
                except Exception as e:
                    logger.error(f"Failed to remove user {user_id}: {e}")
        await asyncio.sleep(60)

# Start Telegram Bot
async def run_bot():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    app.add_handler(ChatMemberHandler(handle_new_member, ChatMemberHandler.CHAT_MEMBER))

    asyncio.create_task(check_unaffirmed_users(app))
    await app.initialize()
    await app.start()
    await app.updater.start_polling()
    await app.updater.wait()

# Combined Main
def main():
    Thread(target=lambda: flask_app.run(host="0.0.0.0", port=10000)).start()
    asyncio.run(run_bot())

if __name__ == "__main__":
    main()
