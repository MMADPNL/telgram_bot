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
        "SELECT coins FROM users WHERE user_id = ?",
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
        DO UPDATE SET coins = excluded.coins
    """, (user_id, coins))

    con.commit()
    con.close()


def add_balance(user_id, amount):
    set_balance(
        user_id,
        get_balance(user_id) + int(amount)
    )


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
        "روی پیام کاربر ریپلای کن و بنویس:\n"
        "انتقال 500"
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

    sender_balance = get_balance(sender_id)

    if sender_balance < amount:
        await update.message.reply_text(
            f"❌ موجودی کافی نیست.\n"
            f"💰 موجودی: {sender_balance:,} 🪙"
        )
        return

    set_balance(
        sender_id,
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
        f"💰 موجودی شما: {get_balance(sender_id):,} 🪙"
    )


# ==================================================
# DEDUCT - OWNER ONLY
# ==================================================

async def deduct(update, amount):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text(
            "❌ فقط صاحب ربات می‌تواند موجودی را کسر کند."
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

    if user is None or user.is_bot:
        return

    if amount <= 0:
        await update.message.reply_text(
            "❌ مبلغ باید بیشتر از صفر باشد."
        )
        return

    old_balance = get_balance(user.id)

    if old_balance < amount:
        await update.message.reply_text(
            f"❌ موجودی کافی نیست.\n"
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
        f"💰 موجودی جدید: {get_balance(user.id):,} 🪙"
    )


# ==================================================
# START GAME
# ==================================================

async def start_game(update, game_type, rounds, bet):
    user_id = update.effective_user.id

    if user_id in games:
        await update.message.reply_text(
            "❌ بازی قبلی شما هنوز تمام نشده."
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

    # مثال:
    # 3تاس 100 = 300 سکه
    # 3بولینگ 100 = 300 سکه
    # 3بستکبال 100 = 300 سکه

    total_bet = rounds * bet
    current_balance = get_balance(user_id)

    if current_balance < total_bet:
        await update.message.reply_text(
            f"❌ موجودی کافی نیست.\n\n"
            f"💰 موجودی: {current_balance:,} 🪙\n"
            f"💸 لازم: {total_bet:,} 🪙"
        )
        return

    # کل شرط فقط یک بار کم می‌شود.
    set_balance(
        user_id,
        current_balance - total_bet
    )

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

    await update.message.reply_text(
        f"{EMOJI[game_type]} بازی شروع شد!\n\n"
        f"🎮 تعداد دور: {rounds}\n"
        f"💸 شرط هر دور: {bet:,} 🪙\n"
        f"💰 کل شرط: {total_bet:,} 🪙\n\n"
        f"🤖 اول ربات {EMOJI[game_type]} می‌اندازد..."
    )

    await bot_throw(update)


# ==================================================
# BOT THROW
# ==================================================

async def bot_throw(update):
    user_id = update.effective_user.id
    game = games.get(user_id)

    if game is None:
        return

    game["bot_score"] = None

    msg = await update.message.reply_dice(
        emoji=game["emoji"]
    )

    game["bot_score"] = msg.dice.value

    await update.message.reply_text(
        f"🤖 ربات: {game['bot_score']}\n\n"
        f"👤 حالا خودت {game['emoji']} بنداز!"
    )


# ==================================================
# USER THROW
# ==================================================

async def user_throw(update, context):
    if update.message is None:
        return

    if update.message.dice is None:
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

        # شرط قبلاً رزرو شده.
        # فقط مبلغ برد به موجودی اضافه می‌شود.
        add_balance(
            user_id,
            bet * 2
        )

        result = (
            f"🏆 بردی!\n"
            f"➕ {bet * 2:,} 🪙"
        )

    elif user_score < bot_score:
        game["losses"] += 1

        # مبلغ دیگری از موجودی کم نمی‌شود.
        result = (
            f"😢 باختی!\n"
            f"➖ {bet:,} 🪙"
        )

    else:
        game["draws"] += 1

        # شرط همین دور برمی‌گردد.
        add_balance(
            user_id,
            bet
        )

        result = (
            f"🤝 مساوی!\n"
            f"↩️ {bet:,} 🪙 برگشت"
        )

    await update.message.reply_text(
        f"🎮 دور {game['current']}\n\n"
        f"🤖 ربات: {bot_score}\n"
        f"👤 تو: {user_score}\n\n"
        f"{result}\n\n"
        f"💰 موجودی: {get_balance(user_id):,} 🪙"
    )

    # دور بعد
    if game["current"] < game["rounds"]:
        game["current"] += 1
        game["bot_score"] = None

        await update.message.reply_text(
            f"🎮 دور {game['current']} از "
            f"{game['rounds']}\n\n"
            f"🤖 اول ربات {game['emoji']} می‌اندازد..."
        )

        await bot_throw(update)
        return

    # پایان بازی
    await update.message.reply_text(
        "🏁 بازی تمام شد!\n\n"
        f"🏆 برد: {game['wins']}\n"
        f"😢 باخت: {game['losses']}\n"
        f"🤝 مساوی: {game['draws']}\n\n"
        f"💰 موجودی نهایی: "
        f"{get_balance(user_id):,} 🪙"
    )

    del games[user_id]


# ==================================================
# TEXT MESSAGES
# ==================================================

async def all_messages(update, context):
    if update.message is None:
        return

    # پرتاب ایموجی را user_throw هندل می‌کند.
    if update.message.dice:
        return

    text = update.message.text

    if not text:
        return

    text = text.strip()

    # ------------------------------
    # انتقال
    # ------------------------------

    if text.startswith("انتقال "):
        parts = text.split()

        if len(parts) != 2:
            await update.message.reply_text(
                "مثال: انتقال 500"
            )
            return

        try:
            amount = int(parts[1])
        except ValueError:
            await update.message.reply_text(
                "مثال: انتقال 500"
            )
            return

        await transfer(update, amount)
        return

    # ------------------------------
    # کسر
    # ------------------------------

    if text.startswith("کسر "):
        parts = text.split()

        if len(parts) != 2:
            await update.message.reply_text(
                "مثال: کسر 500"
            )
            return

        try:
            amount = int(parts[1])
        except ValueError:
            await update.message.reply_text(
                "مثال: کسر 500"
            )
            return

        await deduct(update, amount)
        return

    # ------------------------------
    # بازی
    # ------------------------------

    parts = text.split()

    if len(parts) != 2:
        return

    command = parts[0]

    try:
        bet = int(parts[1])
    except ValueError:
        return

    if not command or not command[0].isdigit():
        return

    rounds = int(command[0])

    if rounds < 1 or rounds > 3:
        await update.message.reply_text(
            "❌ تعداد بازی باید بین 1 تا 3 باشد."
        )
        return

    # تاس
    if "تاس" in command:
        await start_game(
            update,
            "dice",
            rounds,
            bet
        )
        return

    # بولینگ
    if "بولینگ" in command:
        await start_game(
            update,
            "bowling",
            rounds,
            bet
        )
        return

    # بستکبال / بسکتبال
    if "بستکبال" in command or "بسکتبال" in command:
        await start_game(
            update,
            "basketball",
            rounds,
            bet
        )
        return


# ==================================================
# RUN
# ==================================================

init_db()

if not TOKEN:
    raise RuntimeError(
        "BOT_TOKEN تنظیم نشده است."
    )

app = Application.builder().token(TOKEN).build()

app.add_handler(
    CommandHandler("start", start)
)

app.add_handler(
    CommandHandler("coins", coins)
)

app.add_handler(
    MessageHandler(
        filters.Dice.ALL,
        user_throw
    )
)

app.add_handler(
    MessageHandler(
        filters.TEXT & ~filters.COMMAND,
        all_messages
    )
)

print("BOT STARTED")

app.run_polling()
    CommandHandler


