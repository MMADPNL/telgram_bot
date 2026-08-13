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

GAMES = {
    "تاس": ("dice", "🎲", 3000),
    "بولینگ": ("bowling", "🎳", 10000),
    "بستکبال": ("basketball", "🏀", 10000),
    "بسکتبال": ("basketball", "🏀", 10000),
}

active_games = {}


def db():
    return sqlite3.connect(DB)


def init_db():
    with db() as con:
        con.execute(
            "CREATE TABLE IF NOT EXISTS users "
            "(user_id INTEGER PRIMARY KEY, coins INTEGER NOT NULL)"
        )


def balance(uid):
    with db() as con:
        row = con.execute(
            "SELECT coins FROM users WHERE user_id=?",
            (uid,)
        ).fetchone()

        if row is None:
            con.execute(
                "INSERT INTO users(user_id,coins) VALUES(?,?)",
                (uid, START_COINS)
            )
            return START_COINS

        return row[0]


def set_balance(uid, amount):
    with db() as con:
        con.execute(
            "INSERT INTO users(user_id,coins) VALUES(?,?) "
            "ON CONFLICT(user_id) DO UPDATE SET coins=excluded.coins",
            (uid, max(0, int(amount)))
        )


def add_balance(uid, amount):
    set_balance(uid, balance(uid) + amount)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    uid = update.effective_user.id

    await update.message.reply_text(
        "🤖 ربات آماده است!\n\n"
        f"💰 موجودی: {balance(uid):,} 🪙\n\n"
        "🎲 1تاس 100\n"
        "🎳 1بولینگ 100\n"
        "🏀 1بستکبال 100\n\n"
        "برای 3 دور:\n"
        "3تاس 100\n"
        "3بولینگ 100\n"
        "3بستکبال 100\n\n"
        "حداقل شرط: 100\n"
        "حداکثر دور: 3\n"
        "سقف تاس: 3000\n"
        "سقف بولینگ: 10000\n"
        "سقف بسکتبال: 10000\n\n"
        "انتقال: روی پیام کاربر ریپلای کن و بنویس:\n"
        "انتقال 500"
    )


async def coins(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        f"💰 موجودی شما: {balance(update.effective_user.id):,} 🪙"
    )


async def transfer(update, amount):
    sender = update.effective_user.id
    reply = update.message.reply_to_message

    if reply is None:
        await update.message.reply_text(
            "❌ روی پیام گیرنده ریپلای کن.\nمثال: انتقال 500"
        )
        return

    receiver = reply.from_user

    if receiver is None or receiver.is_bot:
        return

    if receiver.id == sender:
        await update.message.reply_text("❌ انتقال به خودت ممکن نیست.")
        return

    if amount <= 0:
        return

    money = balance(sender)

    if money < amount:
        await update.message.reply_text(
            f"❌ موجودی کافی نیست.\n💰 {money:,} 🪙"
        )
        return

    set_balance(sender, money - amount)
    add_balance(receiver.id, amount)

    await update.message.reply_text(
        f"✅ انتقال شد.\n"
        f"👤 {receiver.first_name}\n"
        f"💸 {amount:,} 🪙\n"
        f"💰 موجودی شما: {balance(sender):,} 🪙"
    )


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

    old = balance(user.id)

    if old < amount:
        await update.message.reply_text(
            f"❌ موجودی کافی نیست.\n💰 {old:,}"
        )
        return

    set_balance(user.id, old - amount)

    await update.message.reply_text(
        f"✅ کسر شد.\n"
        f"👤 {user.first_name}\n"
        f"➖ {amount:,} 🪙\n"
        f"💰 موجودی جدید: {balance(user.id):,} 🪙"
    )


async def start_game(update, kind, emoji, max_bet, rounds, bet):
    uid = update.effective_user.id

    if uid in active_games:
        await update.message.reply_text(
            "❌ بازی قبلی هنوز تمام نشده."
        )
        return

    if rounds < 1 or rounds > MAX_ROUNDS:
        await update.message.reply_text(
            "❌ تعداد دور فقط 1 تا 3 است."
        )
        return

    if bet < MIN_BET:
        await update.message.reply_text(
            "❌ حداقل شرط 100 سکه است."
        )
        return

    if bet > max_bet:
        await update.message.reply_text(
            f"❌ سقف شرط این بازی {max_bet:,} سکه است."
        )
        return

    total = rounds * bet
    money = balance(uid)

    if money < total:
        await update.message.reply_text(
            f"❌ موجودی کافی نیست.\n"
            f"💰 موجودی: {money:,}\n"
            f"💸 لازم: {total:,}"
        )
        return

    # کل شرط فقط یک بار برای کل بازی کم می‌شود.
    set_balance(uid, money - total)

    active_games[uid] = {
        "kind": kind,
        "emoji": emoji,
        "rounds": rounds,
        "current": 1,
        "bet": bet,
        "bot": None,
        "wins": 0,
        "losses": 0,
        "draws": 0
    }

    await update.message.reply_text(
        f"{emoji} بازی شروع شد!\n"
        f"🎮 {rounds} دور\n"
        f"💸 شرط هر دور: {bet:,}\n"
        f"💰 کل شرط: {total:,}\n\n"
        f"🤖 ربات اول {emoji} می‌اندازد."
    )

    await bot_throw(update)


async def bot_throw(update):
    uid = update.effective_user.id
    game = active_games.get(uid)

    if game is None:
        return

    msg = await update.message.reply_dice(emoji=game["emoji"])
    game["bot"] = msg.dice.value

    await update.message.reply_text(
        f"🤖 ربات: {game['bot']}\n\n"
        f"👤 حالا خودت {game['emoji']} بنداز!"
    )


async def user_throw(update, context):
    if not update.message or not update.message.dice:
        return

    uid = update.effective_user.id
    game = active_games.get(uid)

    if game is None:
        return

    dice = update.message.dice

    if dice.emoji != game["emoji"]:
        await update.message.reply_text(
            f"❌ الان باید {game['emoji']} بندازی."
        )
        return

    if game["bot"] is None:
        return

    bot_score = game["bot"]
    user_score = dice.value
    bet = game["bet"]

    if user_score > bot_score:
        game["wins"] += 1

        # چون شرط قبلاً کم شده، اینجا فقط برد پرداخت می‌شود.
        add_balance(uid, bet * 2)

        result = f"🏆 بردی! +{bet * 2:,} 🪙"

    elif user_score < bot_score:
        game["losses"] += 1
        result = f"😢 باختی! -{bet:,} 🪙"

    else:
        game["draws"] += 1
        add_balance(uid, bet)
        result = f"🤝 مساوی! +{bet:,} 🪙"

    await update.message.reply_text(
        f"🤖 ربات: {bot_score}\n"
        f"👤 تو: {user_score}\n\n"
        f"{result}\n"
        f"💰 موجودی: {balance(uid):,} 🪙"
    )

    if game["current"] < game["rounds"]:
        game["current"] += 1
        game["bot"] = None

        await update.message.reply_text(
            f"🎮 دور {game['current']} از {game['rounds']}\n"
            f"🤖 ربات اول {game['emoji']} می‌اندازد."
        )

        await bot_throw(update)
        return

    await update.message.reply_text(
        "🏁 بازی تمام شد!\n\n"
        f"🏆 برد: {game['wins']}\n"
        f"😢 باخت: {game['losses']}\n"
        f"🤝 مساوی: {game['draws']}\n\n"
        f"💰 موجودی: {balance(uid):,} 🪙"
    )

    del active_games[uid]


async def messages(update, context):
    if not update.message:
        return

    if update.message.dice:
        return

    text = update.message.text

    if not text:
        return

    text = text.strip()

    if text.startswith("انتقال "):
        p = text.split()

        if len(p) == 2:
            try:
                await transfer(update, int(p[1]))
            except ValueError:
                await update.message.reply_text("مثال: انتقال 500")

        return

    if text.startswith("کسر "):
        p = text.split()

        if len(p) == 2:
            try:
                await deduct(update, int(p[1]))
            except ValueError:
                await update.message.reply_text("مثال: کسر 500")

        return

    p = text.split()

    if len(p) != 2:
        return

    command = p[0]

    try:
        bet = int(p[1])
    except ValueError:
        return

    if not command or not command[0].isdigit():
        return

    rounds = int(command[0])

    for name, data in GAMES.items():
        if name in command:
            kind, emoji, max_bet = data

            await start_game(
                update,
                kind,
                emoji,
                max_bet,
                rounds,
                bet
            )

            return


def main():
    init_db()

    if not TOKEN:
        raise RuntimeError("BOT_TOKEN تنظیم نشده است.")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("coins", coins))

    app.add_handler(
        MessageHandler(
            filters.Dice.ALL,
            user_throw
        )
    )

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
