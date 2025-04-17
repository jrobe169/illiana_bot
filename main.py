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

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Telegram Bot Token
TOKEN = os.getenv("BOT_TOKEN", "your-telegram-bot-token")
GROUP_ID = -1002116956436  # Replace with your actual group ID

# Track members and affirmations
joined_users = {}

# Affirmation keywords
AFFIRM_KEYWORDS = ["i affirm", "affirm", "i agree", "👍"]

# Flask app for Render.com keep-alive
flask_app = Flask(__name__)

@flask_app.route("/")
def index():
    return "Bot is running!"

# Message handler
async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message_text = update.message.text.lower().strip()
    user_id = update.effective_user.id
    chat_id = update.effective_chat.id

    if chat_id != GROUP_ID:
        return

    if any(kw in message_text for kw in AFFIRM_KEYWORDS):
        username = update.effective_user.username or update.effective_user.full_name
        await update.message.reply_text(f"🕊️ Welcome {username}! Your affirmation has been recorded.")
        joined_users.pop(user_id, None)
        logger.info(f"{username} affirmed.")

# New member joins
async def handle_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_member: ChatMember = update.chat_member
    if chat_member.new_chat_member.status == "member":
        user_id = chat_member.from_user.id
        username = chat_member.from_user.username or chat_member.from_user.full_name
        join_time = datetime.now()
        joined_users[user_id] = join_time
        logger.info(f"{username} joined the group.")
        await context.bot.send_message(
            chat_id=GROUP_ID,
            text=f"👋 Welcome {username}! Please affirm your participation by typing 'I Affirm', 'Affirm', 'I Agree', or sending 👍."
        )

# Periodic check
async def check_for_unaffirmed(app: Application):
    while True:
        now = datetime.now()
        to_remove = [user_id for user_id, join_time in joined_users.items() if now - join_time > timedelta(minutes=10)]
        for user_id in to_remove:
            try:
                await app.bot.ban_chat_member(chat_id=GROUP_ID, user_id=user_id)
                await app.bot.unban_chat_member(chat_id=GROUP_ID, user_id=user_id)
                logger.info(f"Removed user {user_id} for not affirming.")
                del joined_users[user_id]
            except Exception as e:
                logger.error(f"Failed to remove user {user_id}: {e}")
        await asyncio.sleep(60)

# Main async run
async def run_bot():
    telegram_app = Application.builder().token(TOKEN).build()

    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    telegram_app.add_handler(ChatMemberHandler(handle_new_member, ChatMemberHandler.CHAT_MEMBER))

    asyncio.create_task(check_for_unaffirmed(telegram_app))
    await telegram_app.run_polling()

# Start everything
def main():
    import threading
    threading.Thread(target=lambda: flask_app.run(host="0.0.0.0", port=10000)).start()
    asyncio.run(run_bot())

if __name__ == "__main__":
    main()
