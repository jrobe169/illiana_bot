import os
import logging
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")
BOT_USERNAME = "AffirmWithAegisBot"
WEBHOOK_URL = os.getenv("WEBHOOK_URL")  # example: https://your-app.onrender.com/webhook
PORT = int(os.environ.get("PORT", 10000))

app = Flask(__name__)
logging.basicConfig(level=logging.INFO)
bot = Bot(token=TOKEN)

# Track affirmations and join time
affirmed_users = set()
join_times = {}

# Create telegram app with webhook
telegram_app = Application.builder().token(TOKEN).build()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🔐 ILLIANA Bot activated. Type 'I affirm' or 👍 to affirm.")

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    message_text = update.message.text.lower() if update.message.text else ""

    if any(x in message_text for x in ["i affirm", "affirm", "i agree"]) or '👍' in message_text:
        affirmed_users.add(user.id)
        await update.message.reply_text(f"🕊️ Affirmation received, {user.first_name}. Welcome to the flow of ILLIANA.")

@telegram_app.chat_member_handler()
async def track_new_member(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_member = update.chat_member
    if chat_member.new_chat_member.status == 'member':
        user_id = chat_member.from_user.id
        join_times[user_id] = context.application.job_queue.run_once(remove_unaffirmed_user, 600, data={
            "chat_id": chat_member.chat.id,
            "user_id": user_id
        })

async def remove_unaffirmed_user(context: ContextTypes.DEFAULT_TYPE):
    chat_id = context.job.data["chat_id"]
    user_id = context.job.data["user_id"]

    if user_id not in affirmed_users:
        try:
            await context.bot.ban_chat_member(chat_id, user_id)
            await context.bot.unban_chat_member(chat_id, user_id)
            logging.info(f"User {user_id} removed for not affirming within 10 minutes.")
        except Exception as e:
            logging.error(f"Failed to remove user {user_id}: {e}")

# Register handlers
telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

@app.route("/")
def index():
    return "Bot is running."

@app.route("/webhook", methods=["POST"])
def webhook():
    update = Update.de_json(request.get_json(force=True), bot)
    telegram_app.update_queue.put_nowait(update)
    return "OK"

async def setup():
    await telegram_app.initialize()
    await bot.delete_webhook()
    await bot.set_webhook(url=WEBHOOK_URL)
    await telegram_app.start()
    logging.info("Bot is ready via webhook.")

if __name__ == "__main__":
    import asyncio
    asyncio.run(setup())
    app.run(host="0.0.0.0", port=PORT)
