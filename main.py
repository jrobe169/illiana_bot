import logging
import os
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters
from datetime import datetime
from flask import Flask
from threading import Thread
import csv
from pathlib import Path

# === CONFIG ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
CSV_LOG = "affirmations_log.csv"

# === TELEGRAM SETUP ===
telegram_app = ApplicationBuilder().token(BOT_TOKEN).build()

def is_affirmation(text):
    return any(phrase in text.lower() for phrase in ["i affirm", "affirm", "i agree"]) or "👍" in text

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    print("💬 Received message:", update.message.text)

    message = update.message
    if not message or not message.text:
        return

    if is_affirmation(message.text):
        user = message.from_user
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        file_exists = Path(CSV_LOG).is_file()

        with open(CSV_LOG, mode="a", newline='', encoding="utf-8") as file:
            writer = csv.writer(file)
            if not file_exists:
                writer.writerow(["Timestamp", "Name", "User ID", "Affirmation"])
            writer.writerow([timestamp, user.full_name, user.id, message.text])

        await message.reply_text(f"🕊️ Affirmation received, {user.first_name}. Welcome to the flow of ILLIANA.")
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == OWNER_ID:
        await update.message.reply_text("🔐 ILLIANA Bot activated.")
    else:
        await update.message.reply_text("⛔ You do not have permission to use this command.")

telegram_app.add_handler(CommandHandler("start", start))
telegram_app.add_handler(MessageHandler(filters.TEXT, handle_message))

# === FLASK SETUP ===
flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "ILLIANA Bot is running."

def run_flask():
    flask_app.run(host="0.0.0.0", port=10000)

async def run_bot_forever():
    await telegram_app.initialize()
    await telegram_app.start()
    print("🤖 Bot started.")
    # This replaces run_polling()
    await telegram_app.bot.set_my_commands([
        ("start", "Activate the bot"),
    ])
    # Let the bot idle forever
    while True:
        await asyncio.sleep(3600)

if __name__ == "__main__":
    # Start Flask server in background
    Thread(target=run_flask).start()

    # Start Telegram bot without run_polling()
    loop = asyncio.get_event_loop()
    loop.create_task(run_bot_forever())
    loop.run_forever()
