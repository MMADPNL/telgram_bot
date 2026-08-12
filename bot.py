import os
import random

from supabase import create_client
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

MY_ID = 8552447077
MY_START_COINS = 1_000_000
USER_START_COINS = 1_000

MIN_BET = 100
MAX_BET = 10_000

if not TOKEN:
    raise RuntimeError("BOT_TOKEN تنظیم نشده است")

if not SUPABASE_URL or not SUPABASE_KEY:
    raise RuntimeError("SUPABASE_URL یا SUPABASE_KEY تنظیم نشده است")

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)


def get_coins(user_id):
    result = (
        supabase
        .table("users")
        .select("coins")
        .eq("user_id", user_id)
        .execute()
    )

    if result.data:
        return result.data[0]["coins"]

    start_coins = MY_START_COINS if user_id == MY_ID else USER_START_COINS

    supabase.table("users").insert({
        "user_id": user_id,
        "coins": start_coins,
    }).execute()

    return start_coins


def set_coins(user_id, amount):
    supabase.table("users").update({
        "coins": amount
    }).eq("user_id", user_id).execute()


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    balance = get_coins(user_id)

    keyboard = [
        ["🎲 تاس", "⚽ فوتبال"],
        ["🎳 بولینگ", "💰 سکه"],
    ]

    await update.message.reply_text(
        "🤖 ربات بازی آماده است!\n\n"
        f"🪙 موجودی شما: {balance:,} سکه\n\n"
        "🎲 تاس:\n"
        "1تاس 100\n\n"
        "🎳 بولینگ:\n"
        "1بولینگ 100\n\n"
        "💸 انتقال:\n"
        "روی پیام شخص ریپلای کن و بنویس:\n"
        "انتقال 500\n\n"
        "حداقل شرط: 100 🪙\n"
        "حداکثر شرط: 10,000 🪙",
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )
    )


async def coins_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    balance = get_coins(user_id)

    await update.message.reply_text(
        f"💰 موجودی شما:\n\n"
        f"🪙 {balance:,} سکه"
    )


async def transfer_coins(update: Update, amount: int):
    sender_id = update.effective_user.id
    message = update.message

    if not message.reply_to_message:
        await message.reply_text(
            "❌ باید روی پیام شخص موردنظر ریپلای کنی.\n\n"
            "مثال:\n"
            "انتقال 500"
        )
        return

    receiver = message.reply_to_message.from_user

    if receiver.is_bot:
        await message.reply_text("❌ نمی‌توانی به ربات سکه بدهی.")
        return

    receiver_id = receiver.id

    if sender_id == receiver_id:
        await message.reply_text(
            "❌ نمی‌توانی به خودت سکه انتقال بدهی."
        )
        return

    if amount <= 0:
        await message.reply_text(
            "❌ مقدار انتقال باید بیشتر از صفر باشد."
        )
        return

    sender_balance = get_coins(sender_id)

    if sender_balance < amount:
        await message.reply_text(
            f"❌ موجودی کافی نیست.\n"
            f"🪙 موجودی
