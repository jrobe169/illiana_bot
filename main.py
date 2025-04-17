
import logging
import os
from telegram import Update
from telegram.ext import ApplicationBuilder, ContextTypes, MessageHandler, CommandHandler, filters
from datetime import datetime
from flask import Flask, request

# === CONFIG ===
BOT_TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = int(os.getenv("OWNER_ID"))
LOG_FILE = "affirmations_log.txt"

# === TELEGRAM SETUP ===
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
        log_entry = f"{timestamp} - {user.full_name} ({user.id}): {message.text}\n"

        with open(LOG_FILE, "a") as file:
            file.write(log_entry)

        await message.reply_text(f"🕊️ Affirmation received, {user.first_name}. Welcome to the flow of ILLIANA.")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_user.id == OWNER_ID:
        await update.message.reply_text("🔐 ILLIANA Bot activated.")
    else:
        await update.message.reply_text("⛔ You do not have permission to use this command.")

app.add_handler(CommandHandler("start", start))
app.add_handler(MessageHandler(filters.TEXT, handle_message))

# === FLASK SETUP FOR RENDER DEPLOYMENT ===
flask_app = Flask(__name__)

@flask_app.route("/")
def home():
    return "ILLIANA Affirmation Bot is running."

@flask_app.route("/start-bot")
def start_bot():
    import threading
    threading.Thread(target=lambda: app.run_polling()).start()
    return "Bot started!"

if __name__ == "__main__":
    flask_app.run(host="0.0.0.0", port=10000)
