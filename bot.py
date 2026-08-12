import os
import random

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        ["🎲 تاس", "⚽ فوتبال"],
        ["🎳 بولینگ", "💰 سکه"],
    ]

    reply_markup = ReplyKeyboardMarkup(
        keyboard,
        resize_keyboard=True
    )

    await update.message.reply_text(
        "🎮 به ربات بازی خوش اومدی!\n\n"
        "یکی از بازی‌ها رو انتخاب کن 👇",
        reply_markup=reply_markup
    )


async def dice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    score = random.randint(1, 6)

    await update.message.reply_text(
        f"🎲 عدد تاس: {score}\n"
        f"🪙 سکه: {score}"
    )


async def football(update: Update, context: ContextTypes.DEFAULT_TYPE):
    score = random.randint(1, 100)

    await update.message.reply_text(
        f"⚽ امتیاز فوتبال: {score}\n"
        f"🪙 سکه: {score}"
    )


async def bowling(update: Update, context: ContextTypes.DEFAULT_TYPE):
    score = random.randint(1, 100)

    await update.message.reply_text(
        f"🎳 امتیاز بولینگ: {score}\n"
        f"🪙 سکه: {score}"
    )


async def coins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "💰 موجودی شما:\n"
        "🪙 0 سکه\n\n"
        "سیستم سکه در مرحله بعد فعال میشه."
    )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text

    if text == "🎲 تاس":
        await dice(update, context)

    elif text == "⚽ فوتبال":
        await football(update, context)

    elif text == "🎳 بولینگ":
        await bowling(update, context)

    elif text == "💰 سکه":
        await coins(update, context)


def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN تنظیم نشده است")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("dice", dice))
    app.add_handler(CommandHandler("football", football))
    app.add_handler(CommandHandler("bowling", bowling))
    app.add_handler(CommandHandler("coins", coins))

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            button_handler
        )
    )

    print("Bot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()
