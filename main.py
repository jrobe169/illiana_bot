import logging
import asyncio
from datetime import datetime, timedelta

from flask import Flask
from telegram import Update, ChatMember
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ChatMemberHandler,
)

TOKEN = "YOUR_BOT_TOKEN"  # Replace with your bot token
GROUP_ID = -1001234567890  # Replace with your actual group ID

affirmation_keywords = {"i affirm", "affirm", "i agree", "👍"}
user_join_times = {}

logging.basicConfig(level=logging.INFO)

telegram_app = ApplicationBuilder().token(TOKEN).build()
flask_app = Flask(__name__)


# --- Telegram Bot Logic --- #

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔐 ILLIANA Bot activated.")


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    user = message.from_user
    user_id = user.id
    text = message.text.lower().strip()

    if any(keyword in text for keyword in affirmation_keywords):
        logging.info(f"Affirmation received from {user.full_name}")
        await message.reply_text(
            f"🕊️ Affirmation received, {user.first_name}. Welcome to the flow of ILLIANA."
        )
        user_join_times.pop(user_id, None)
    else:
        logging.info(f"Message received from {user.full_name}: {message.text}")


async def track_user_join(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result: ChatMember = update.chat_member
    new_status = result.new_chat_member.status
    user = result.new_chat_member.user
    user_id = user.id

    if new_status == "member":
        logging.info(f"{user.full_name} joined the group.")
        user_join_times[user_id] = datetime.utcnow()


async def check_unaffirmed_users():
    while True:
        await asyncio.sleep(60)  # Run every minute
        now = datetime.utcnow()
        for user_id, join_time in list(user_join_times.items()):
            if now - join_time > timedelta(minutes=10):
                try:
                    await telegram_app.bot.ban_chat_member(chat_id=GROUP_ID, user_id=user_id)
                    await telegram_app.bot.unban_chat_member(chat_id=GROUP_ID, user_id=user_id)
                    logging.info(f"Removed {user_id} for not affirming.")
                    user_join_times.pop(user_id, None)
                except Exception as e:
                    logging.error(f"Failed to remove user {user_id}: {e}")


@flask_app.route("/")
def index():
    return "ILLiANA Bot is running."


def main():
    telegram_app.add_handler(CommandHandler("start", start))
    telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))
    telegram_app.add_handler(ChatMemberHandler(track_user_join, ChatMemberHandler.CHAT_MEMBER))

    telegram_app.run_polling(non_stop=True)


if __name__ == "__main__":
    loop = asyncio.get_event_loop()
    loop.create_task(check_unaffirmed_users())
    main()
