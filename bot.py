import os
import sqlite3
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

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


# =========================
# DATABASE
# =========================

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
            "INSERT INTO users VALUES (?, ?)",
            (user_id, coins)
        )

        con.commit()
    else:
        coins = row[0]

    con.close()
    return coins


def set_balance(user_id, coins):
    con = sqlite3.connect(DB)
    cur = con.cursor()

    cur.execute("""
        INSERT INTO users(user_id, coins)
        VALUES (?, ?)
        ON CONFLICT(user_id)
        DO UPDATE SET coins=excluded.coins
    """, (user_id, max(0, int(coins))))

    con.commit()
    con.close()


def add_balance(user_id, amount):
    set_balance(
        user_id,
        balance(user_id) + amount
    )


# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        "🤖 ربات آماده است!\n\n"
        f"💰 موجودی: {balance(update.effective_user.id):,} 🪙\n\n"

        "🎲 1تاس 100\n"
        "🎳 1بولینگ 100\n"
        "🏀 1بستکبال 100\n\n"

        "حداقل شرط: 100 🪙\n"
        "تاس حداکثر: 3000 🪙\n"
        "بولینگ حداکثر: 10000 🪙\n"
        "بسکتبال حداکثر: 10000 🪙\n"
        "حداکثر دور: 3"
    )


# =========================
# COINS
# =========================

async def coins(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(
        f"💰 موجودی شما:\n"
        f"{balance(update.effective_user.id):,} 🪙"
    )


# =========================
# TRANSFER
# =========================

async def transfer(update, amount):

    sender = update.effective_user.id
    reply = update.message.reply_to_message

    if not reply:
        await update.message.reply_text(
            "❌ روی پیام گیرنده ریپلای کن.\n"
            "مثال: انتقال 500"
        )
        return

    receiver = reply.from_user

    if not receiver or receiver.is_bot:
        return

    if receiver.id == sender:
        await update.message.reply_text(
            "❌ نمی‌توانی به خودت انتقال بدهی."
        )
        return

    if amount <= 0:
        return

    sender_balance = balance(sender)

    if sender_balance < amount:
        await update.message.reply_text(
            f"❌ موجودی کافی نیست.\n"
            f"💰 {sender_balance:,} 🪙"
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
        f"💰 موجودی شما: {balance(sender):,} 🪙"
    )


# =========================
# DEDUCT
# =========================

async def deduct(update, amount):

    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text(
            "❌ فقط صاحب ربات."
        )
        return

    reply = update.message.reply_to_message

    if not reply:
        await update.message.reply_text(
            "❌ روی پیام کاربر ریپلای کن.\n"
            "مثال: کسر 500"
        )
        return

    user = reply.from_user

    if not user or user.is_bot:
        return

    old = balance(user.id)

    if old < amount:
        await update.message.reply_text(
            f"❌ موجودی کافی نیست.\n"
            f"💰 {old:,} 🪙"
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
        f"💰 موجودی جدید: {balance(user.id):,} 🪙"
    )


# =========================
# START GAME
# =========================

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

    total = bet * rounds

    old_balance = balance(user_id)

    if old_balance < total:
        await update.message.reply_text(
            f"❌ موجودی کافی نیست.\n\n"
            f"💰 موجودی: {old_balance:,}\n"
            f"💸 لازم: {total:,}"
        )
        return

    # کل شرط از اول رزرو می‌شود
    set_balance(
        user_id,
        old_balance - total
    )

    games[user_id] = {
        "type": game_type,
        "emoji": EMOJI[game_type],
        "rounds": rounds,
        "current": 1,
        "bet": bet,
        "bot_score": None,
        "wins": 0,
        "losses": 0,
        "draws": 0,
    }

    await update.message.reply_text(
        f"{EMOJI[game_type]} بازی شروع شد!\n\n"
        f"🎮 دور: {rounds}\n"
        f"💸 شرط هر دور: {bet:,}\n\n"
        "🤖 اول ربات می‌اندازد..."
    )

    await bot_throw(update)


# =========================
# BOT THROW
# =========================

async def bot_throw(update):

    user_id = update.effective_user.id
    game = games.get(user_id)

    if not game:
        return

    msg = await update.message.reply_dice(
        emoji=game["emoji"]
    )

    game["bot_score"] = msg.dice.value

    await update.message.reply_text(
        f"🤖 ربات: {game['bot_score']}\n\n"
        f"👤 حالا خودت {game['emoji']} بنداز!"
    )


# =========================
# USER THROW
# =========================

async def user_throw(update):

    if not update.message or not update.message.dice:
        return

    user_id = update.effective_user.id
    game = games.get(user_id)

    if not game:
        return

    dice = update.message.dice

    # فقط ایموجی همان بازی قبول شود
    if dice.emoji != game["emoji"]:
        await update.message.reply_text(
            f"❌ الان باید {game['emoji']} بندازی."
        )
        return

    bot_score = game["bot_score"]
    user_score = dice.value
    bet = game["bet"]

    if user_score > bot_score:

        game["wins"] += 1

        # برد = دریافت 2 برابر شرط
        add_balance(
            user_id,
            bet * 2
        )

        result = f"🏆 بردی! +{bet * 2:,} 🪙"

    elif user_score < bot_score:

        game["losses"] += 1

        result = f"😢 باختی! -{bet:,} 🪙"

    else:

        game["draws"] += 1

        # مساوی = برگشت شرط
        add_balance(
            user_id,
            bet
        )

        result = f"🤝 مساوی! +{bet:,} 🪙"

    await update.message.reply_text(
        f"🤖 ربات: {bot_score}\n"
        f"👤 تو: {user_score}\n\n"
        f"{result}\n\n"
        f"💰 موجودی: {balance(user_id):,} 🪙"
    )

    # دور بعد
    if game["current"] < game["rounds"]:

        game["current"] += 1

        await update.message.reply_text(
            f"🎮 دور {game['current']} از "
            f"{game['rounds']}\n\n"
            "🤖 اول ربات می‌اندازد..."
        )

        await bot_throw(update)
        return

    # پایان
    await update.message.reply_text(
        "🏁 بازی تمام شد!\n\n"
        f"🏆 برد: {game['wins']}\n"
        f"😢 باخت: {game['losses']}\n"
        f"🤝 مساوی: {game['draws']}\n\n"
        f"💰 موجودی: {balance(user_id):,} 🪙"
    )

    del games[user_id]


# =========================
# ALL MESSAGES
# =========================

async def all_messages(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not update.message:
        return

    # پرتاب واقعی تلگرام
    if update.message.dice:
        await user_throw(update)
        return

    text = update.message.text

    if not text:
        return

    text = text.strip()

    # -------------------------
    # انتقال
    # -------------------------

    if text.startswith("انتقال "):

        try:
            amount = int(text.split()[1])
            await transfer(update, amount)
        except:
            await update.message.reply_text(
                "مثال: انتقال 500"
            )

        return

    # -------------------------
    # کسر
    # -------------------------

    if text.startswith("کسر "):

        try:
            amount = int(text.split()[1])
            await deduct(update, amount)
        except:
            await update.message.reply_text(
                "مثال: کسر 500"
            )

        return

    # -------------------------
    # بازی‌ها
    # -------------------------

    parts = text.split()

    if len(parts) != 2:
        return

    command = parts[0]

    try:
        bet = int(parts[1])
    except:
        return

    # استخراج تعداد دور
    try:
        rounds = int(command[0])
    except:
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

    # بسکتبال
    if "بستکبال" in command or "بسکتبال" in command:

        await start_game(
            update,
            "basketball",
            rounds,
            bet
        )
        return


# =========================
# RUN
# =========================

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
        filters.ALL,
        all_messages
    )
)

print("BOT STARTED")

app.run_polling()
