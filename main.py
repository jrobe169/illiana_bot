import logging
import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters
from datetime import datetime
from flask import Flask

# === CONFIG ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
LOG_FILE = "affirmations_log.txt"

# === TELEGRAM SETUP ===
telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()

def is_affirmation(text):
    return any(phrase in text.lower() for phrase in ["i affirm", "affirm", "i agree"]) or "👍" in text

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    message = update.message
    if not message or not message.text:
        return

    if is_affirmation(message.text):
        user = message.from_user
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_entry = f"{timestamp} - {user.full_name} ({user.id}): {message.text}\n"

        with open(LOG_FILE, "a") as file:
            file.write(log_entry)

        await message.reply_text(f"🕊️ Affirmation received, {user.first_name}. Welcome to the flow of ILLIANA.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == OWNER_ID:
        await update.message.reply_text("🔐 ILLIANA Bot activated.")
    else:
        await update.message.reply_text("⛔ You do not have permission to use this command.")

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT, handle_message))

# === FLASK SETUP FOR RENDER DEPLOYMENT ===
flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "ILLIANA Affirmation Bot is running."

async def run_all():
    await telegram_app.initialize()
    await telegram_app.start()
    await telegram_app.updater.start_polling()
    # Keep alive
    await telegram_app.updater.idle()

if __name__ == "__main__":
    # Start Flask in a separate thread
    from threading import Thread
    Thread(target=lambda: flask_app.run(host="0.0.0.0", port=10000)).start()

    # Run the Telegram bot in main thread using asyncio
    asyncio.run(run_all())
