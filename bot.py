import os
import sqlite3

from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
)


TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = 8552447077

DB = "bot_data.db"

START_COINS = 100000
MIN_BET = 100
MAX_ROUNDS = 3


# =========================================================
# GAME SETTINGS
# =========================================================

GAME_SETTINGS = {
    "dice": {
        "emoji": "🎲",
        "names": ("تاس",),
        "max_bet": 3000,
    },
    "bowling": {
        "emoji": "🎳",
        "names": ("بولینگ",),
        "max_bet": 10000,
    },
    "basketball": {
        "emoji": "🏀",
        "names": ("بستکبال", "بسکتبال"),
        "max_bet": 10000,
    },
}


# بازی‌های در حال اجرا
active_games = {}


# =========================================================
# DATABASE
# =========================================================

def init_db():
    with sqlite3.connect(DB) as con:
        con.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                coins INTEGER NOT NULL
            )
            """
        )


def balance(user_id):
    with sqlite3.connect(DB) as con:
        row = con.execute(
            "SELECT coins FROM users WHERE user_id = ?",
            (user_id,)
        ).fetchone()

        if row is None:
            con.execute(
                "INSERT INTO users (user_id, coins) VALUES (?, ?)",
                (user_id, START_COINS)
            )
            return START_COINS

        return int(row[0])


def set_balance(user_id, amount):
    amount = max(0, int(amount))

    with sqlite3.connect(DB) as con:
        con.execute(
            """
            INSERT INTO users (user_id, coins)
            VALUES (?, ?)
            ON CONFLICT(user_id)
            DO UPDATE SET coins = excluded.coins
            """,
            (user_id, amount)
        )


def add_balance(user_id, amount):
    set_balance(
        user_id,
        balance(user_id) + int(amount)
    )


# =========================================================
# START
# =========================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    await update.message.reply_text(
        "🤖 ربات آماده است!\n\n"
        f"💰 موجودی: {balance(user_id):,} 🪙\n\n"

        "🎲 تاس\n"
        "1تاس 100\n"
        "3تاس 100\n\n"

        "🎳 بولینگ\n"
        "1بولینگ 100\n"
        "3بولینگ 100\n\n"

        "🏀 بسکتبال\n"
        "1بستکبال 100\n"
        "3بستکبال 100\n\n"

        "━━━━━━━━━━━━\n\n"

        "💰 حداقل شرط: 100\n"
        "🎮 حداکثر دور: 3\n"
        "🎲 سقف تاس: 3000\n"
        "🎳 سقف بولینگ: 10000\n"
        "🏀 سقف بسکتبال: 10000\n\n"

        "💸 انتقال:\n"
        "روی پیام کاربر ریپلای کن:\n"
        "انتقال 500\n\n"

        "🔧 کسر:\n"
        "صاحب ربات روی پیام کاربر ریپلای کند:\n"
        "کسر 500"
    )


# =========================================================
# COINS
# =========================================================

async def coins(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    await update.message.reply_text(
        f"💰 موجودی شما:\n\n"
        f"{balance(user_id):,} 🪙"
    )


# =========================================================
# TRANSFER
# =========================================================

async def transfer(update, amount):

    sender_id = update.effective_user.id
    reply = update.message.reply_to_message

    if reply is None:
        await update.message.reply_text(
            "❌ روی پیام گیرنده ریپلای کن.\n"
            "مثال: انتقال 500"
        )
        return

    receiver = reply.from_user

    if receiver is None or receiver.is_bot:
        return

    if receiver.id == sender_id:
        await update.message.reply_text(
            "❌ نمی‌توانی به خودت انتقال بدهی."
        )
        return

    if amount <= 0:
        await update.message.reply_text(
            "❌ مبلغ باید بیشتر از صفر باشد."
        )
        return

    sender_balance = balance(sender_id)

    if sender_balance < amount:
        await update.message.reply_text(
            f"❌
