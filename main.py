import logging
from telegram import Update, ChatMemberUpdated
from telegram.ext import (
    ApplicationBuilder, CommandHandler, ContextTypes, MessageHandler, filters,
    ChatMemberHandler
)
from datetime import datetime, timedelta
import asyncio
import os

TOKEN = os.getenv("BOT_TOKEN")
user_affirmed = {}
join_times = {}

logging.basicConfig(level=logging.INFO)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔐 ILLIANA Bot activated.")

async def handle_affirmation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    chat_id = update.effective_chat.id

    if user and any(trigger in update.message.text.lower() for trigger in ["i affirm", "i agree", "affirm", "👍"]):
        user_affirmed[user.id] = True
        await update.message.reply_text(
            f"🕊️ Affirmation received, {user.first_name}. Welcome to the flow of ILLIANA."
        )

async def track_new_members(update: Update, context: ContextTypes.DEFAULT_TYPE):
    result = update.chat_member
    status_change = result.difference()

    if status_change is None:
        return

    if result.new_chat_member.status == "member":
        user = result.new_chat_member.user
        join_times[user.id] = datetime.utcnow()
        user_affirmed[user.id] = False

        logging.info(f"Tracking {user.first_name} ({user.id}) for affirmation")

        await asyncio.sleep(600)  # 10 minutes

        if not user_affirmed.get(user.id, False):
            try:
                await context.bot.send_message(
                    chat_id=update.chat_member.chat.id,
                    text=f"⏳ {user.first_name}, you were invited into the flow but didn’t affirm. Please return when you're ready. 🙏"
                )
                await context.bot.ban_chat_member(update.chat_member.chat.id, user.id)
                await context.bot.unban_chat_member(update.chat_member.chat.id, user.id)  # Optional: allows rejoin
                logging.info(f"Removed {user.first_name} ({user.id}) for not affirming in time.")
            except Exception as e:
                logging.error(f"Failed to remove user: {e}")

if __name__ == "__main__":
    app = ApplicationBuilder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_affirmation))
    app.add_handler(ChatMemberHandler(track_new_members, ChatMemberHandler.CHAT_MEMBER))

    logging.info("Bot is starting...")
    app.run_polling()
