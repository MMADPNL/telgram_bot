import os
import sqlite3
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")
OWNER_ID = 8552447077

DB = "bot_data.db"
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

games = {}


# -----------------------------
# DATABASE
# -----------------------------

def init_db():
    with sqlite3.connect(DB) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                coins INTEGER NOT NULL
            )
        """)


def get_balance(user_id):
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


def set_balance(user_id, coins):
    coins = max(0, int(coins))

    with sqlite3.connect(DB) as con:
        con.execute("""
            INSERT INTO users (user_id, coins)
            VALUES (?, ?)
            ON CONFLICT(user_id)
            DO UPDATE SET coins = excluded.coins
        """, (user_id, coins))


def add_balance(user_id, amount):
    set_balance(
        user_id,
        get_balance(user_id) + int(amount)
    )


# -----------------------------
# START
# -----------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    await update.message.reply_text(
        "🤖 ربات آماده است!\n\n"
        f"💰 موجودی: {get_balance(user_id):,} 🪙\n\n"
        "🎲 1تاس 100\n"
        "🎳 1بولینگ 100\n"
        "🏀 1بستکبال 100\n\n"
        "برای چند دور:\n"
        "3تاس 100\n"
        "3بولینگ 100\n"
        "3بستکبال 100\n\n"
        "حداقل شرط: 100\n"
        "حداکثر دور: 3\n"
        "حداکثر شرط تاس: 3000\n"
        "حداکثر شرط بولینگ: 10000\n"
        "حداکثر شرط بسکتبال: 10000"
    )


# -----------------------------
# COINS
# -----------------------------

async def coins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"💰 موجودی شما: {get_balance(update.effective_user.id):,} 🪙"
    )


# -----------------------------
# TRANSFER
# -----------------------------

async def transfer(update, amount):
    reply = update.message.reply_to_message

    if reply is None:
        await update.message.reply_text(
            "❌ روی پیام کاربر ریپلای کن.\nمثال: انتقال 500"
        )
        return

    receiver = reply.from_user
    sender_id = update.effective_user.id

    if receiver is None or receiver.is_bot:
        return

    if receiver.id == sender_id:
        await update.message.reply_text("❌ نمی‌توانی به خودت انتقال بدهی.")
        return

    if amount <= 0:
        await update.message.reply_text("❌ مبلغ نامعتبر است.")
        return

    sender_coins = get_balance(sender_id)

    if sender_coins < amount:
        await update.message.reply_text(
            f"❌ موجودی کافی نیست.\n💰 {sender_coins:,} 🪙"
        )
        return

    set_balance(sender_id, sender_coins - amount)
    add_balance(receiver.id, amount)

    await update.message.reply_text(
        f"✅ انتقال انجام شد!\n"
        f"👤 {receiver.first_name}\n"
        f"💸 {amount:,} 🪙\n"
        f"💰 موجودی شما: {get_balance(sender_id):,} 🪙"
    )


# -----------------------------
# DEDUCT
# -----------------------------

async def deduct(update, amount):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ فقط صاحب ربات.")
        return

    reply = update.message.reply_to_message

    if reply is None:
        await update.message.reply_text(
            "❌ روی پیام کاربر ریپلای کن.\nمثال: کسر 500"
        )
        return

    user = reply.from_user

    if user is None or user.is_bot:
        return

    old = get_balance(user.id)

    if old < amount:
        await update.message.reply_text(
            f"❌ موجودی کافی نیست.\n💰 {old:,} 🪙"
        )
        return

    set_balance(user.id, old - amount)

    await update.message.reply_text(
        f"✅ کسر شد!\n"
        f"👤 {user.first_name}\n"
        f"➖ {amount:,} 🪙\n"
        f"💰 موجودی جدید: {get_balance(user.id):,} 🪙"
    )


# -----------------------------
# START GAME
# -----------------------------

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
            f"❌ حداکثر شرط این بازی {MAX_BET[game_type]:,} سکه است."
        )
        return

    # مثال:
    # 3تاس 100 = 300 سکه
    total_bet = rounds * bet

    coins_now = get_balance(user_id)

    if coins_now < total_bet:
        await update.message.reply_text(
            f"❌ موجودی کافی نیست.\n"
            f"💰 موجودی: {coins_now:,}\n"
            f"💸 لازم: {total_bet:,}"
        )
        return

    # شرط کل بازی فقط یک بار کم می‌شود.
    set_balance(
        user_id,
        coins_now - total_bet
    )

    games[user_id] = {
        "type": game_type,
        "emoji": EMOJI[game_type],
        "rounds": rounds,
        "round": 1,
        "bet": bet,
        "bot_score": None,
        "wins": 0,
        "losses": 0,
        "draws": 0
    }

    await update.message.reply_text(
        f"{EMOJI[game_type]} بازی شروع شد!\n\n"
        f"🎮 دورها: {rounds}\n"
        f"💸 شرط هر دور: {bet:,}\n"
        f"💰 کل شرط: {total_bet:,}\n\n"
        f"🤖 اول ربات {EMOJI[game_type]} می‌اندازد."
    )

    await bot_throw(update)


# -----------------------------
# BOT THROW
# -----------------------------

async def bot_throw(update):
    user_id = update.effective_user.id
    game = games.get(user_id)

    if game is None:
        return

    msg = await update.message.reply_dice(
        emoji=game["emoji"]
    )

    game["bot_score"] = msg.dice.value

    await update.message.reply_text(
        f"🤖 ربات: {game['bot_score']}\n\n"
        f"👤 حالا خودت {game['emoji']} بنداز!"
    )


# -----------------------------
# USER THROW
# -----------------------------

async def user_throw(update, context):
    if not update.message or not update.message.dice:
        return

    user_id = update.effective_user.id
    game = games.get(user_id)

    if game is None:
        return

    dice = update.message.dice

    if dice.emoji != game["emoji"]:
        await update.message.reply_text(
            f"❌ الان باید {game['emoji']} بندازی."
        )
        return

    if game["bot_score"] is None:
        return

    bot_score = game["bot_score"]
    user_score = dice.value
    bet = game["bet"]

    if user_score > bot_score:
        game["wins"] += 1

        # شرط قبلاً کم شده؛ فقط جایزه اضافه می‌شود.
        add_balance(user_id, bet * 2)

        result = f"🏆 بردی! +{bet * 2:,} 🪙"

    elif user_score < bot_score:
        game["losses"] += 1

        result = f"😢 باختی! -{bet:,} 🪙"

    else:
        game["draws"] += 1

        # شرط همان دور برمی‌گردد.
        add_balance(user_id, bet)

        result = f"🤝 مساوی! +{bet:,} 🪙"

    await update.message.reply_text(
        f"🤖 ربات: {bot_score}\n"
        f"👤 تو: {user


