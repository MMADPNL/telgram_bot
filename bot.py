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

games = {}


# ==================================================
# START
# ==================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    await update.message.reply_text(
        "🤖 ربات آماده است!\n\n"
        f"💰 موجودی: {get_balance(user_id):,} 🪙\n\n"

        "🎲 تاس:\n"
        "1تاس 100\n"
        "3تاس 100\n\n"

        "🎳 بولینگ:\n"
        "1بولینگ 100\n"
        "3بولینگ 100\n\n"

        "🏀 بسکتبال:\n"
        "1بستکبال 100\n"
        "3بستکبال 100\n\n"

        "━━━━━━━━━━━━\n"
        "💰 حداقل شرط: 100\n"
        "🎲 حداکثر شرط تاس: 3000\n"
        "🎳 حداکثر شرط بولینگ: 10000\n"
        "🏀 حداکثر شرط بسکتبال: 10000\n"
        "🎮 حداکثر دور: 3\n\n"

        "💸 انتقال:\n"
        "روی پیام کاربر ریپلای کن:\n"
        "انتقال 500"
    )


# ==================================================
# DATABASE
# ==================================================

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


def get_balance(user_id):

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
        get_balance(user_id) + amount
    )


# ==================================================
# COINS
# ==================================================

async def coins(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    await update.message.reply_text(
        f"💰 موجودی شما:\n\n"
        f"{get_balance(user_id):,} 🪙"
    )


# ==================================================
# TRANSFER
# ==================================================

async def transfer(update, amount):

    sender = update.effective_user.id

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

    if receiver.id == sender:
        await update.message.reply_text(
            "❌ نمی‌توانی به خودت انتقال بدهی."
        )
        return

    if amount <= 0:
        return

    sender_balance = get_balance(sender)

    if sender_balance < amount:
        await update.message.reply_text(
            f"❌ موجودی کافی نیست.\n"
            f"💰 موجودی: {sender_balance:,}"
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
        f"👤 {receiver.first_name}\n"
        f"💸 {amount:,} 🪙\n"
        f"💰 موجودی شما: {get_balance(sender):,} 🪙"
    )


# ==================================================
# DEDUCT OWNER
# ==================================================

async def deduct(update, amount):

    if update.effective_user.id != OWNER_ID:

        await update.message.reply_text(
            "❌ فقط صاحب ربات."
        )
        return

    reply = update.message.reply_to_message

    if reply is None:
        await update.message.reply_text(
            "❌ روی پیام کاربر ریپلای کن.\n"
            "مثال: کسر 500"
        )
        return

    user = reply.from_user

    old = get_balance(user.id)

    if old < amount:

        await update.message.reply_text(
            f"❌ موجودی کافی نیست.\n"
            f"💰 {old:,}"
        )
        return

    set_balance(
        user.id,
        old - amount
    )

    await update.message.reply_text(
        "✅ کسر شد!\n\n"
        f"👤 {user.first_name}\n"
        f"➖ {amount:,} 🪙\n"
        f"💰 موجودی جدید: {get_balance(user.id):,} 🪙"
    )


# ==================================================
# START GAME
# ==================================================

async def start_game(update, game_type, rounds, bet):

    user_id = update.effective_user.id

    if user_id in games:

        await update.message.reply_text(
            "❌ بازی قبلی هنوز تمام نشده."
        )
        return

    if rounds < 1 or rounds > MAX_ROUNDS:

        await update.message.reply_text(
            "❌ تعداد دور باید بین 1 تا 3 باشد."
        )
        return

    if bet < MIN_BET:

        await update.message.reply_text(
            "❌ حداقل شرط 100 سکه است."
        )
        return

    if bet > MAX_BET[game_type]:

        await update.message.reply_text(
            f"❌ حداکثر شرط این بازی "
            f"{MAX_BET[game_type]:,} سکه است."
        )
        return

    # ==================================================
    # خیلی مهم:
    # 3تاس 100 = فقط 300 سکه
    # 3بولینگ 100 = فقط 300 سکه
    # 3بستکبال 100 = فقط 300 سکه
    # ==================================================

    total_bet = rounds * bet

    user_balance = get_balance(user_id)

    if user_balance < total_bet:

        await update.message.reply_text(
            f"❌ موجودی کافی نیست.\n\n"
            f"💰 موجودی: {user_balance:,} 🪙\n"
            f"💸 لازم: {total_bet:,} 🪙"
        )
        return

    # فقط یک بار کل شرط رزرو می‌شود
    set_balance(
        user_id,
        user_balance - total_bet
    )

    games[user_id] = {
        "type": game_type,
        games[user_id] = 
games[user_id] = {
    "type": game_type,
    "emoji": EMOJI[game_type],
    "rounds": rounds,
    "current": 1,
    "bet": bet,
    "total_bet": total_bet,
    "bot_score": None,
    "wins": 0,
    "losses": 0,
    "draws": 0,
}
