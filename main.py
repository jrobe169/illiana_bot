import logging
import os
import csv
from pathlib import Path
from datetime import datetime
from flask import Flask
from threading import Thread
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters

# === CONFIG ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
CSV_LOG = "affirmations_log.csv"

# === LOGGING ===
logging.basicConfig(level=logging.INFO)

# === TELEGRAM APP ===
app = ApplicationBuilder().token(BOT_TOKEN).build()

def is_affirmation(text):
    return any(phrase in text.lower() for phrase in ["i affirm", "affirm", "i agree"]) or "👍" in text

async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
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

        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text=f"🕊️ Affirmation received, {user.first_name}. Welcome to the flow of ILLIANA."
        )

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == OWNER_ID:
        await update.message.reply_text("🔐 ILLIANA Bot activated.")
    else:
        await update.message.reply_text("⛔ You do not have permission to use this command.")

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT & (~filters.COMMAND), handle_message))

# === FLASK SERVER FOR KEEP-ALIVE ===
flask_app = Flask(__name__)

@flask_app.route("/")
def index():
    return "ILLIANA Bot is running."

def run_flask():
    flask_app.run(host="0.0.0.0", port=10000)

# === RUN BOT ===
def run_bot():
    app.run_polling()

if __name__ == "__main__":
    Thread(target=run_flask).start()
    run_bot()
