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
START_COINS = 100000

MIN_BET = 100
MAX_ROUNDS = 3

MAX_BET = {
    "dice": 3000,
    "bowling": 10000,
    "basketball": 10000,
}

EMOJI = {
    "dice": "🎲",
    "bowling": "🎳",
    "basketball": "🏀",
}

DB = "bot_data.db"

# بازی فعال هر کاربر
games = {}


# =====================================================
# DATABASE
# =====================================================

def init_db():
    con = sqlite3.connect(DB)
    cur = con.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            coins INTEGER NOT NULL
        )
    """)

    con.commit()
    con.close()


def balance(user_id):
    con = sqlite3.connect(DB)
    cur = con.cursor()

    cur.execute(
        "SELECT coins FROM users WHERE user_id=?",
        (user_id,)
    )

    row = cur.fetchone()

    if row is None:
        coins = START_COINS

        cur.execute(
            "INSERT INTO users (user_id, coins) VALUES (?, ?)",
            (user_id, coins)
        )

        con.commit()
    else:
        coins = row[0]

    con.close()

    return int(coins)


def set_balance(user_id, coins):
    coins = max(0, int(coins))

    con = sqlite3.connect(DB)
    cur = con.cursor()

    cur.execute("""
        INSERT INTO users (user_id, coins)
        VALUES (?, ?)
        ON CONFLICT(user_id)
        DO UPDATE SET coins=excluded.coins
    """, (user_id, coins))

    con.commit()
    con.close()


def add_balance(user_id, amount):
    set_balance(
        user_id,
        balance(user_id) + int(amount)
    )


# =====================================================
# START
# =====================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    await update.message.reply_text(
        "🤖 ربات آماده است!\n\n"
        f"💰 موجودی: {balance(user_id):,} 🪙\n\n"

        "🎲 بازی تاس:\n"
        "1تاس 100\n\n"

        "🎳 بازی بولینگ:\n"
        "1بولینگ 100\n\n"

        "🏀 بازی بسکتبال:\n"
        "1بستکبال 100\n\n"

        "━━━━━━━━━━━━\n"
        "💰 حداقل شرط: 100\n"
        "🎲 حداکثر تاس: 3000\n"
        "🎳 حداکثر بولینگ: 10000\n"
        "🏀 حداکثر بسکتبال: 10000\n"
        "🎮 حداکثر دور: 3\n\n"

        "💸 انتقال:\n"
        "روی پیام کاربر ریپلای کن و بنویس:\n"
        "انتقال 500"
    )


# =====================================================
# COINS
# =====================================================

async def coins(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    await update.message.reply_text(
        f"💰 موجودی شما:\n\n"
        f"{balance(user_id):,} 🪙"
    )


# =====================================================
# TRANSFER
# =====================================================

async def transfer(update, amount):

    sender = update.effective_user.id

    reply = update.message.reply_to_message

    if reply is None:
        await update.message.reply_text(
            "❌ روی پیام کاربر ریپلای کن.\n\n"
            "مثال:\n"
            "انتقال 500"
        )
        return

    receiver = reply.from_user

    if receiver is None or receiver.is_bot:
        await update.message.reply_text(
            "❌ کاربر معتبر نیست."
        )
        return

    if receiver.id == sender:
        await update.message.reply_text(
            "❌ نمی‌توانی به خودت انتقال بدهی."
        )
        return

    if amount <= 0:
        await update.message.reply_text(
            "❌ مبلغ نامعتبر است."
        )
        return

    sender_balance = balance(sender)

    if sender_balance < amount:
        await update.message.reply_text(
            f"❌ موجودی کافی نیست.\n\n"
            f"💰 موجودی: {sender_balance:,} 🪙"
        )
        return

    set_balance(
        sender,
        sender_balance - amount
    )

    add_balance(
        receiver.id,
        amount
    )

    await update.message.reply_text(
        "✅ انتقال انجام شد!\n\n"
        f"👤 گیرنده: {receiver.first_name}\n"
        f"💸 مبلغ: {amount:,} 🪙\n"
        f"💰 موجودی شما: {balance(sender):,} 🪙"
    )


# =====================================================
# DEDUCT
# =====================================================

async def deduct(update, amount):

    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text(
            "❌ فقط صاحب ربات می‌تواند کسر کند."
        )
        return

    reply = update.message.reply_to_message

    if reply is None:
        await update.message.reply_text(
            "❌ روی پیام کاربر ریپلای کن.\n\n"
            "مثال:\n"
            "کسر 500"
        )
        return

    user = reply.from_user

    if user is None or user.is_bot:
        return

    old_balance = balance(user.id)

    if old_balance < amount:
        await update.message.reply_text(
            f"❌ موجودی کافی نیست.\n\n"
            f"💰 موجودی: {old_balance:,} 🪙"
        )
        return

    set_balance(
        user.id,
        old_balance - amount
    )

    await update.message.reply_text(
        "✅ موجودی کسر شد!\n\n"
        f"👤 {user.first_name}\n"
        f"➖ {amount:,} 🪙\n"
        f"💰 موجودی جدید: {balance(user.id):,} 🪙"
    )


# =====================================================
# START GAME
# =====================================================

async def start_game(update, game_type, rounds, bet):

    user_id = update.effective_user.id

    # یک کاربر همزمان فقط یک بازی
    if user_id in games:
        await update.message.reply_text(
            "❌ بازی قبلی هنوز تمام نشده."
        )
        return

    if rounds < 1 or rounds > MAX_ROUNDS:
        await update.message.reply
