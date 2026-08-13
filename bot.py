import os
import sqlite3
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters

TOKEN = os.getenv("BOT_TOKEN")

OWNER_ID = 8552447077

DB_FILE = "bot.db"

START_OWNER = 100000
START_USER = 100

MIN_BET = 100

MAX_BET = {
    "dice": 3000,
    "bowling": 10000,
    "basketball": 10000,
}

MAX_ROUNDS = 3

games = {}


# =========================
# DATABASE
# =========================

def connect():
    return sqlite3.connect(DB_FILE)


def init_db():
    con = connect()
    cur = con.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER PRIMARY KEY,
            coins INTEGER NOT NULL
        )
    """)

    con.commit()
    con.close()


def get_coins(user_id):

    con = connect()
    cur = con.cursor()

    cur.execute(
        "SELECT coins FROM users WHERE user_id=?",
        (user_id,)
    )

    row = cur.fetchone()

    if row is None:

        amount = START_OWNER if user_id == OWNER_ID else START_USER

        cur.execute(
            "INSERT INTO users(user_id, coins) VALUES(?, ?)",
            (user_id, amount)
        )

        con.commit()

    else:
        amount = row[0]

    con.close()

    return amount


def set_coins(user_id, amount):

    con = connect()
    cur = con.cursor()

    cur.execute("""
        INSERT INTO users(user_id, coins)
        VALUES(?, ?)
        ON CONFLICT(user_id)
        DO UPDATE SET coins=excluded.coins
    """, (user_id, amount))

    con.commit()
    con.close()


def add_coins(user_id, amount):
    set_coins(user_id, get_coins(user_id) + amount)


# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    await update.message.reply_text(
        "🤖 ربات بازی فعال است!\n\n"
        f"💰 موجودی: {get_coins(user_id):,} 🪙\n\n"

        "🎲 تاس:\n"
        "1تاس 100\n"
        "حداکثر شرط: 3000\n\n"

        "🎳 بولینگ:\n"
        "1بولینگ 100\n"
        "حداکثر شرط: 10000\n\n"

        "🏀 بسکتبال:\n"
        "1بستکبال 100\n"
        "یا 1بسکتبال 100\n"
        "حداکثر شرط: 10000\n\n"

        "🎮 تعداد دور: حداکثر 3\n\n"

        "💸 انتقال:\n"
        "روی پیام شخص ریپلای کن:\n"
        "انتقال 500\n\n"

        "💰 موجودی:\n"
        "/coins"
    )


# =========================
# COINS
# =========================

async def coins_command(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    await update.message.reply_text(
        f"💰 موجودی شما:\n\n"
        f"🪙 {get_coins(user_id):,}"
    )


# =========================
# CHARGE
# =========================

async def charge(update: Update, amount):

    user_id = update.effective_user.id

    if user_id != OWNER_ID:

        await update.message.reply_text(
            "❌ این دستور فقط برای صاحب ربات است."
        )

        return

    if amount <= 0:

        await update.message.reply_text(
            "❌ مبلغ نامعتبر است."
        )

        return

    add_coins(user_id, amount)

    await update.message.reply_text(
        f"✅ شارژ شد.\n\n"
        f"➕ {amount:,} 🪙\n"
        f"💰 موجودی: {get_coins(user_id):,} 🪙"
    )


# =========================
# TRANSFER
# =========================

async def transfer(update: Update, amount):

    sender = update.effective_user.id

    if not update.message.reply_to_message:

        await update.message.reply_text(
            "❌ باید روی پیام شخص ریپلای کنی.\n\n"
            "مثال:\n"
            "انتقال 500"
        )

        return

    receiver_user = update.message.reply_to_message.from_user

    if receiver_user.is_bot:

        await update.message.reply_text(
            "❌ نمی‌توانی به ربات انتقال بدهی."
        )

        return

    receiver = receiver_user.id

    if sender == receiver:

        await update.message.reply_text(
            "❌ نمی‌توانی به خودت انتقال بدهی."
        )

        return

    if amount <= 0:

        await update.message.reply_text(
            "❌ مبلغ نامعتبر است."
        )

        return

    sender_balance = get_coins(sender)

    if sender_balance < amount:

        await update.message.reply_text(
            f"❌ موجودی کافی نیست.\n"
            f"💰 موجودی: {sender_balance:,} 🪙"
        )

        return

    receiver_balance = get_coins(receiver)

    set_coins(sender, sender_balance - amount)
    set_coins(receiver, receiver_balance + amount)

    await update.message.reply_text(
        "✅ انتقال انجام شد!\n\n"
        f"👤 گیرنده: {receiver_user.first_name}\n"
        f"💸 مبلغ: {amount:,} 🪙\n"
        f"💰 موجودی شما: {get_coins(sender):,} 🪙"
    )


# =========================
# START GAME
# =========================

async def start_game(update: Update, text):

    user_id = update.effective_user.id

    if user_id in games:

        await update.message.reply_text(
            "❌ شما یک بازی در حال انجام دارید."
        )

        return

    parts = text.split()

    if len(parts) != 2:
        return

    command = parts[0]

    try:
        bet = int(parts[1])
    except ValueError:

        await update.message.reply_text(
            "❌ مبلغ شرط باید عدد باشد."
        )

        return

    # -------------------------
    # تعداد دور
    # -------------------------

    if not command[0].isdigit():
        return

    rounds = int(command[0])

    if rounds < 1 or rounds > MAX_ROUNDS:

        await update.message.reply_text(
            "❌ تعداد بازی حداکثر 3 است."
        )

        return

    # -------------------------
    # نوع بازی
    # -------------------------

    if "تاس" in command:

        game_type = "dice"
        emoji = "🎲"
        name = "تاس"

    elif "بولینگ" in command:

        game_type = "bowling"
        emoji = "🎳"
        name = "بولینگ"

    elif "بستکبال" in command or "بسکتبال" in command:

        game_type = "basketball"
        emoji = "🏀"
        name = "بسکتبال"

    else:
        return

    max_bet = MAX_BET[game_type]

    # -------------------------
    # شرط
    # -------------------------

    if bet < MIN_BET:

        await update.message.reply_text(
            "❌ حداقل شرط 100 سکه است."
        )

        return

    if bet > max_bet:

        await update.message.reply_text(
            f"❌ حداکثر شرط {max_bet:,} سکه است."
        )

        return

    total = bet * rounds

    balance = get_coins(user_id)

    if balance < total:

        await update.message.reply_text(
            f"❌ موجودی کافی نیست.\n\n"
            f"💰 موجودی: {balance:,}\n"
            f"💸 لازم: {total:,}"
        )

        return

    # کم کردن شرط
    set_coins(
        user_id,
        balance - total
    )

    games[user_id] = {
        "type": game_type,
        "emoji": emoji,
        "name": name,
        "bet": bet,
        "rounds": rounds,
        "current": 1,
        "bot_score": None,
        "wins": 0,
        "losses": 0,
        "draws": 0,
        "profit": 0,
    }

    await update.message.reply_text(
        f"{emoji} {name} شروع شد!\n\n"
        f"🎮 تعداد دور: {rounds}\n"
        f"💸 شرط هر دور: {bet:,} 🪙\n\n"
        "🤖 اول ربات می‌اندازد..."
    )

    await bot_roll(update, user_id)


# =========================
# BOT ROLL
# =========================

async def bot_roll(update: Update, user_id):

    game = games[user_id]

    msg = await update.message.reply_dice(
        emoji=game["emoji"]
    )

    game["bot_score"] = msg.dice.value

    await update.message.reply_text(
        f"🤖 نتیجه ربات: {game['bot_score']}\n\n"
        f"👤 حالا خودت {game['emoji']} رو بنداز."
    )


# =========================
# USER DICE
# =========================

async def user_dice(update: Update):

    if not update.message or not update.message.dice:
        return

    user_id = update.effective_user.id

    if user_id not in games:
        return

    game = games[user_id]

    dice = update.message.dice

    # فقط همان ایموجی بازی
    if dice.emoji != game["emoji"]:

        await update.message.reply_text(
            f"❌ الان باید {game['emoji']} بندازی."
        )

        return

    player_score = dice.value
    bot_score = game["bot_score"]
    bet = game["bet"]

    # -------------------------
    # برد
    # -------------------------

    if player_score > bot_score:

        prize = bet * 2

        add_coins(user_id, prize)

        game["wins"] += 1
        game["profit"] += bet

        result = (
            "🏆 بردی!\n"
            f"➕ جایزه: {prize:,} 🪙"
        )

    # -------------------------
    # باخت
    # -------------------------

    elif player_score < bot_score:

        game["losses"] += 1
        game["profit"] -= bet

        result = (
            "😢 باختی!\n"
            f"➖ {bet:,} 🪙"
        )

    # -------------------------
    # مساوی
    # -------------------------

    else:

        add_coins(user_id, bet)

        game["draws"] += 1

        result = (
            "🤝 مساوی شد!\n"
            f"↩️ {bet:,} 🪙 برگشت داده شد."
        )

    await update.message.reply_text(
        f"🤖 ربات: {bot_score}\n"
        f"👤 تو: {player_score}\n\n"
        f"{result}\n\n"
        f"💰 موجودی: {get_coins(user_id):,} 🪙"
    )

    # -------------------------
    # دور بعد
    # -------------------------

    if game["current"] < game["rounds"]:

        game["current"] += 1

        await update.message.reply_text(
            f"\n{game['emoji']} دور بعد!\n"
            "🤖 اول ربات می‌اندازد..."
        )

        await bot_roll(update, user_id)

        return

    # -------------------------
    # پایان
    # -------------------------

    await update.message.reply_text(
        "🏁 بازی تمام شد!\n\n"
        f"🏆 برد: {game['wins']}\n"
        f"😢 باخت: {game['losses']}\n"
        f"🤝 مساوی: {game['draws']}\n\n"
        f"📊 سود/زیان: {game['profit']:+,} 🪙\n"
        f"💰 موجودی نهایی: {get_coins(user_id):,} 🪙"
    )

    del games[user_id]


# =========================
# ALL MESSAGES
# =========================

async def all_messages(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not update.message:
        return

    # اگر کاربر Dice فرستاده
    if update.message.dice:

        await user_dice(update)

        return

    # اگر متن نیست
    if not update.message.text:
        return

    text = update.message.text.strip()

    # انتقال
    if text.startswith("انتقال "):

        parts = text.split()

        if len(parts) != 2:
            return

        try:
            amount = int(parts[1])
        except ValueError:
            return

        await transfer(update, amount)

        return

    # شارژ صاحب
    if text.startswith("شارژ "):

        parts = text.split()

        if len(parts) != 2:
            return

        try:
            amount = int(parts[1])
        except ValueError:
            return

        await charge(update, amount)

        return

    # بازی
    if (
        "تاس" in text
        or "بولینگ" in text
        or "بستکبال" in text
        or "بسکتبال" in text
    ):

        await start_game(update, text)

        return


# =========================
# MAIN
# =========================

def main():

    if not TOKEN:
        raise RuntimeError(
            "BOT_TOKEN پیدا نشد."
        )

    init_db()

    app = (
        Application.builder()
        .token(TOKEN)
        .build()
    )

    app.add_handler(
        CommandHandler("start", start)
    )

    app.add_handler(
        CommandHandler("coins", coins_command)
    )

    # همه پیام‌ها از همین‌جا بررسی می‌شوند
    app.add_handler(
        MessageHandler(
            filters.ALL,
            all_messages
        )
    )

    print("BOT STARTED")

    app.run_polling()


if __name__ == "__main__":
    main()
