import os
import random
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎮 به ربات بازی خوش اومدی!\n\n"
        "🎲 /dice تاس\n"
        "⚽ /football فوتبال\n"
        "🎳 /bowling بولینگ"
    )

async def dice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    score = random.randint(1, 6)
    await update.message.reply_text(f"🎲 عدد تاس: {score}\n🪙 سکه: {score}")

async def football(update: Update, context: ContextTypes.DEFAULT_TYPE):
    score = random.randint(1, 100)
    await update.message.reply_text(f"⚽ امتیاز فوتبال: {score}\n🪙 سکه: {score}")

async def bowling(update: Update, context: ContextTypes.DEFAULT_TYPE):
    score = random.randint(1, 100)
    await update.message.reply_text(f"🎳 امتیاز بولینگ: {score}\n🪙 سکه: {score}")

def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN تنظیم نشده است")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("dice", dice))
    app.add_handler(CommandHandler("football", football))
    app.add_handler(CommandHandler("bowling", bowling))

    print("Bot is running...")
    app.run_polling()

if __name__ == "__main__":
    main()
