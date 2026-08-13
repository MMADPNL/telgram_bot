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
        "max_bet": 3000,
    },
    "bowling": {
        "emoji": "🎳",
        "max_bet": 10000,
    },
    "basketball": {
        "emoji": "🏀",
        "max_bet": 10000,
    },
}

active_games = {}


# =========================================================
# DATABASE
# =========================================================

def init_db():
    with sqlite3.connect(DB) as con:
        con.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                coins INTEGER NOT NULL
            )
        """)


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
        con.execute("""
            INSERT INTO users (user_id, coins)
            VALUES (?, ?)
            ON CONFLICT(user_id)
            DO UPDATE SET coins = excluded.coins
        """, (user_id, amount))


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
        f"💰 موجودی شما: {balance(sender_id):,} 🪙"
    )


# =========================================================
# DEDUCT
# =========================================================

async def deduct(update, amount):

    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text(
            "❌ فقط صاحب ربات می‌تواند کسر کند."
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
            "❌ مبلغ نامعتبر است."
        )
        return

    old_balance = balance(user.id)

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
        f"💰 موجودی جدید: {balance(user.id):,} 🪙"
    )


# =========================================================
# START GAME
# =========================================================

async def start_game(update, game_type, rounds, bet):

    user_id = update.effective_user.id

    if user_id in active_games:
        await update.message.reply_text(
            "❌ بازی قبلی هنوز تمام نشده."
        )
        return

    settings = GAME_SETTINGS[game_type]

    emoji = settings["emoji"]
    max_bet = settings["max_bet"]

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

    if bet > max_bet:
        await update.message.reply_text(
            f"❌ سقف شرط این بازی "
            f"{max_bet:,} سکه است."
        )
        return

    total_bet = rounds * bet
    current_balance = balance(user_id)

    if current_balance < total_bet:
        await update.message.reply_text(
            f"❌ موجودی کافی نیست.\n\n"
            f"💰 موجودی: {current_balance:,}\n"
            f"💸 لازم: {total_bet:,}"
        )
        return

    # کل شرط فقط یک بار کم می‌شود
    set_balance(
        user_id,
        current_balance - total_bet
    )

    active_games[user_id] = {
        "game_type": game_type,
        "emoji": emoji,

        "rounds": rounds,
        "current_round": 1,

        "bet": bet,
        "total_bet": total_bet,

        "bot_score": None,

        "wins": 0,
        "losses": 0,
        "draws": 0,

        "waiting_for_user": False,

        # آیدی پیام راهنمایی که کاربر باید روی آن ریپلای کند
        "user_prompt_id": None,
    }

    await update.message.reply_text(
        f"{emoji} بازی شروع شد!\n\n"
        f"🎮 تعداد دور: {rounds}\n"
        f"💸 شرط هر دور: {bet:,} 🪙\n"
        f"💰 کل شرط: {total_bet:,} 🪙\n\n"
        f"🤖 ربات اول {emoji} می‌اندازد..."
    )

    await bot_throw(update)


# =========================================================
# BOT THROW
# =========================================================

async def bot_throw(update):

    user_id = update.effective_user.id
    game = active_games.get(user_id)

    if game is None:
        return

    game["waiting_for_user"] = False
    game["bot_score"] = None
    game["user_prompt_id"] = None

    emoji = game["emoji"]

    # پرتاب ربات
    dice_message = await update.message.reply_dice(
        emoji=emoji
    )

    game["bot_score"] = dice_message.dice.value

    # پیام راهنمای مخصوص همین دور
    prompt = await update.message.reply_text(
        f"🤖 ربات: {game['bot_score']}\n\n"
        f"👤 حالا روی همین پیام ریپلای کن و {emoji} بنداز!\n\n"
        f"⚠️ فقط پرتابی که روی این پیام ریپلای شده باشد قبول می‌شود."
    )

    # ذخیره آیدی پیام راهنما
    game["user_prompt_id"] = prompt.message_id

    # کاربر حالا اجازه پرتاب دارد
    game["waiting_for_user"] = True


# =========================================================
# USER THROW
# =========================================================

async def user_throw(update, context):

    if update.message is None:
        return

    dice = update.message.dice

    if dice is None:
        return

    user_id = update.effective_user.id
    game = active_games.get(user_id)

    if game is None:
        return

    # هنوز نوبت کاربر نیست
    if game["waiting_for_user"] is not True:
        return

    # =====================================================
    # حتماً باید Reply باشد
    # =====================================================

    reply = update.message.reply_to_message

    if reply is None:
        await update.message.reply_text(
            f"❌ اول روی پیام ربات ریپلای کن، "
            f"بعد {game['emoji']} بنداز."
        )
        return

    # فقط Reply به پیام راهنمای همین دور قبول است
    if reply.message_id != game["user_prompt_id"]:
        await update.message.reply_text(
            f"❌ روی پیام آخر ربات ریپلای کن، "
            f"بعد {game['emoji']} بنداز."
        )
        return

    # =====================================================
    # بررسی ایموجی
    # =====================================================

    expected_emoji = game["emoji"]

    if dice.emoji != expected_emoji:
        await update.message.reply_text(
            f"❌ الان بازی {expected_emoji} است.\n\n"
            f"لطفاً روی پیام ربات ریپلای کن و "
            f"{expected_emoji} بنداز."
        )
        return

    # =====================================================
    # قفل فوری برای جلوگیری از پرتاب دوم
    # =====================================================

    game["waiting_for_user"] = False

    bot_score = game["bot_score"]

    if bot_score is None:
        return

    user_score = dice.value
    bet = game["bet"]

    # =====================================================
    # WIN
    # =====================================================

    if user_score > bot_score:

        game["wins"] += 1

        # شرط قبلاً کم شده
        add_balance(
            user_id,
            bet * 2
        )

        result = (
            "🏆 بردی!\n"
            f"➕ {bet * 2:,} 🪙"
        )

    # =====================================================
    # LOSS
    # =====================================================

    elif user_score < bot_score:

        game["losses"] += 1

        # شرط قبلاً کم شده
        result = (
            "😢 باختی!\n"
            f"➖ {bet:,} 🪙"
        )

    # =====================================================
    # DRAW
    # =====================================================

    else:

        game["draws"] += 1

        # فقط شرط همین دور برمی‌گردد
        add_balance(
            user_id,
            bet
        )

        result = (
            "🤝 مساوی!\n"
            f"↩️ {bet:,} 🪙 برگشت"
        )

    # =====================================================
    # RESULT
    # =====================================================

    await update.message.reply_text(
        f"🎮 دور {game['current_round']} "
        f"از {game['rounds']}\n\n"
        f"🤖 ربات: {bot_score}\n"
        f"👤 تو: {user_score}\n\n"
        f"{result}\n\n"
        f"💰 موجودی: {balance(user_id):,} 🪙"
    )

    # =====================================================
    # NEXT ROUND
    # =====================================================

    if game["current_round"] < game["rounds"]:

        game["current_round"] += 1
        game["bot_score"] = None
        game["waiting_for_user"] = False
        game["user_prompt_id"] = None

        await update.message.reply_text(
            f"🎮 دور {game['current_round']} "
            f"از {game['rounds']}\n\n"
            f"🤖 ربات اول {game['emoji']} می‌اندازد..."
        )

        await bot_throw(update)
        return

    # =====================================================
    # GAME FINISHED
    # =====================================================

    await update.message.reply_text(
        "🏁 بازی تمام شد!\n\n"
        f"🏆 برد: {game['wins']}\n"
        f"😢 باخت: {game['losses']}\n"
        f"🤝 مساوی: {game['draws']}\n\n"
        f"💰 موجودی نهایی: "
        f"{balance(user_id):,} 🪙"
    )

    active_games.pop(user_id, None)


# =========================================================
# TEXT MESSAGES
# =========================================================

async def messages(update, context):

    if update.message is None:
        return

    # Dice اینجا پردازش نمی‌شود
    if update.message.dice is not None:
        return

    text = update.message.text

    if not text:
        return

    text = text.strip()

    # =====================================================
    # TRANSFER
    # =====================================================

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

    # =====================================================
    # DEDUCT
    # =====================================================

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

    # =====================================================
    # GAME COMMAND
    # =====================================================

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


# =========================================================
# MAIN
# =========================================================

def main():

    init_db()

    if not TOKEN:
        raise RuntimeError(
            "BOT_TOKEN تنظیم نشده است."
        )

    app = Application.builder().token(TOKEN).build()

    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    app.add_handler(
        CommandHandler(
            "coins",
            coins
        )
    )

    # پرتاب‌های واقعی تلگرام
    app.add_handler(
        MessageHandler(
            filters.Dice.ALL,
            user_throw
        )
    )

    # پیام‌های متنی
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            messages
        )
    )

    print("BOT STARTED")

    app.run_polling()


if __name__ == "__main__":
    main()
