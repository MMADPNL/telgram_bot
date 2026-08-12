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

# =========================
# تنظیمات
# =========================

OWNER_ID = 8552447077

OWNER_START_COINS = 100_000
USER_START_COINS = 100

MIN_BET = 100

DICE_MAX_BET = 3_000
BOWLING_MAX_BET = 10_000
BASKETBALL_MAX_BET = 10_000

MAX_ROUNDS = 3

DB_FILE = "bot_data.db"


# =========================
# دیتابیس
# =========================

def get_db():
    return sqlite3.connect(DB_FILE)


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            coins INTEGER NOT NULL
        )
    """)

    conn.commit()
    conn.close()


def get_coins(user_id):
    conn = get_db()
    cur = conn.cursor()

    cur.execute(
        "SELECT coins FROM users WHERE user_id = ?",
        (user_id,)
    )

    row = cur.fetchone()

    if row is None:

        if user_id == OWNER_ID:
            amount = OWNER_START_COINS
        else:
            amount = USER_START_COINS

        cur.execute(
            "INSERT INTO users (user_id, coins) VALUES (?, ?)",
            (user_id, amount)
        )

        conn.commit()

    else:
        amount = row[0]

    conn.close()

    return amount


def set_coins(user_id, amount):
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO users (user_id, coins)
        VALUES (?, ?)
        ON CONFLICT(user_id)
        DO UPDATE SET coins = excluded.coins
    """, (user_id, amount))

    conn.commit()
    conn.close()


def add_coins(user_id, amount):
    set_coins(
        user_id,
        get_coins(user_id) + amount
    )


def remove_coins(user_id, amount):
    set_coins(
        user_id,
        get_coins(user_id) - amount
    )


# =========================
# بازی‌های فعال
# =========================

games = {}


# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    await update.message.reply_text(
        "🤖 ربات بازی آماده است!\n\n"
        f"💰 موجودی: {get_coins(user_id):,} 🪙\n\n"

        "🎲 تاس:\n"
        "1تاس 100\n"
        "حداکثر شرط: 3000\n\n"

        "🎳 بولینگ:\n"
        "1بولینگ 100\n"
        "حداکثر شرط: 10000\n\n"

        "🏀 بسکتبال:\n"
        "1بستکبال 100\n"
        "یا:\n"
        "1بسکتبال 100\n"
        "حداکثر شرط: 10000\n\n"

        "🎮 تعداد دور در هر بازی: حداکثر 3\n\n"

        "💸 انتقال:\n"
        "روی پیام کاربر ریپلای کن و بنویس:\n"
        "انتقال 500\n\n"

        "💰 موجودی:\n"
        "/coins"
    )


# =========================
# COINS
# =========================

async def coins_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user_id = update.effective_user.id

    await update.message.reply_text(
        f"💰 موجودی شما:\n\n"
        f"🪙 {get_coins(user_id):,}"
    )


# =========================
# شارژ صاحب
        
