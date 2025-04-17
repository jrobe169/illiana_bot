import logging
import os
import asyncio
from datetime import datetime, timedelta
from telegram import Update, ChatMember
from telegram.ext import (
    Application,
    MessageHandler,
    filters,
    ChatMemberHandler,
    ContextTypes,
)
from flask import Flask
from threading import Thread

# Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Environment & Bot Setup
TOKEN = os.getenv("BOT_TOKEN", "your-telegram-bot-token")
GROUP_ID = -1002116956436  # Replace with your group's actual ID
AFFIRM_KEYWORDS = ["i affirm", "affirm", "i agree", "👍"]
joined_users = {}

# Flask server
flask_app = Flask(__name__)
@flask_app.route("/")
def home():
    return "Bot is online!"

# Handler for affirmations
async def handle_affirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip().lower()
    if any(word in text for word in AFFIRM_KEYWORDS):
        joined_users.pop(user_id, None)
        username = update.effective_user.username or update.effective_user.full_name
        await update.message.reply_text(f"🕊️ Thank you {username}, your affirmation has been recorded.")
        logger.info(f"{username} affirmed.")

# Handler for new members
async def handle_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    member: ChatMember = update.chat_member
    if member.new_chat_member.status == "member":
        user_id = member.from_user.id
        joined_users[user_id] = datetime.now()
        username = member.from_user.username or member.from_user.full_name
        await context.bot.send_message(
            chat_id=GROUP_ID,
            text=f"👋 Welcome {username}! Please affirm by typing 'I Affirm', 'Affirm', 'I Agree' or sending 👍 within 10 minutes."
        )
        logger.info(f"{username} joined the group.")

# Task to remove users who didn't affirm
async def monitor_unaffirmed_users(app: Application):
    while True:
        now = datetime.now()
        for user_id, joined_at in list(joined_users.items()):
            if now - joined_at > timedelta(minutes=10):
                try:
                    await app.bot.ban_chat_member(GROUP_ID, user_id)
                    await app.bot.unban_chat_member(GROUP_ID, user_id)
                    logger.info(f"Removed user {user_id} for not affirming in time.")
                    del joined_users[user_id]
                except Exception as e:
                    logger.error(f"Error removing user {user_id}: {e}")
        await asyncio.sleep(60)

# Start the bot
async def run_bot():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_affirmation))
    app.add_handler(ChatMemberHandler(handle_new_member, ChatMemberHandler.CHAT_MEMBER))
    asyncio.create_task(monitor_unaffirmed_users(app))
    await app.run_polling()

# Combined runner
def main():
    Thread(target=lambda: flask_app.run(host="0.0.0.0", port=10000)).start()
    asyncio.run(run_bot())

if __name__ == "__main__":
    main()
