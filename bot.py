import os
import random

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")

# موجودی سکه کاربران
coins = {}

MIN_BET = 100
MAX_BET = 10000


def get_coins(user_id):
    return coins.get(user_id, 1000)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    if user_id not in coins:
        coins[user_id] = 1000

    keyboard = [
        ["🎲 تاس", "⚽ فوتبال"],
        ["🎳 بولینگ", "💰 سکه"],
    ]

    await update.message.reply_text(
        "🤖 ربات بازی آماده است!\n\n"
        f"🪙 موجودی شما: {coins[user_id]} سکه\n\n"
        "برای بازی شرطی در گروه بنویس:\n"
        "🎲 1تاس 100\n"
        "🎳 1بولینگ 100\n\n"
        "حداقل شرط: 100 🪙\n"
        "حداکثر شرط: 10000 🪙",
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )
    )


async def coins_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    await update.message.reply_text(
        f"💰 موجودی شما:\n"
        f"🪙 {get_coins(user_id)} سکه"
    )


async def dice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎲 برای بازی بنویس:\n1تاس 100")


async def football(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("⚽ برای بازی فوتبال فعلاً از منوی بازی استفاده کن.")


async def bowling(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("🎳 برای بازی بنویس:\n1بولینگ 100")


async def bet_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    user_id = user.id
    text = update.message.text.strip()

    parts = text.split()

    if len(parts) != 2:
        return

    game = parts[0]
    bet_text = parts[1]

    if game not in ["1تاس", "1بولینگ"]:
        return

    try:
        bet = int(bet_text)
    except ValueError:
        await update.message.reply_text(
            "❌ مبلغ شرط باید عدد باشد.\n"
            "مثال: 1تاس 100"
        )
        return

    if bet < MIN_BET:
        await update.message.reply_text(
            "❌ حداقل شرط 100 سکه است."
        )
        return

    if bet > MAX_BET:
        await update.message.reply_text(
            "❌ حداکثر شرط 10000 سکه است."
        )
        return

    balance = get_coins(user_id)

    if balance < bet:
        await update.message.reply_text(
            f"❌ موجودی کافی نیست.\n"
            f"🪙 موجودی: {balance}\n"
            f"💰 شرط: {bet}"
        )
        return

    # کم کردن شرط
    coins[user_id] = balance - bet

    if game == "1تاس":
        bot_score = random.randint(1, 6)

        await update.message.reply_text(
            f"🎲 بازی تاس شروع شد!\n\n"
            f"💰 شرط: {bet} 🪙\n"
            f"🤖 تاس ربات: {bot_score}\n\n"
            f"👤 حالا خودت تاس بنداز!"
        )

        context.user_data["game"] = "dice"
        context.user_data["bet"] = bet
        context.user_data["bot_score"] = bot_score

    elif game == "1بولینگ":
        bot_score = random.randint(0, 100)

        await update.message.reply_text(
            f"🎳 بازی بولینگ شروع شد!\n\n"
            f"💰 شرط: {bet} 🪙\n"
            f"🤖 امتیاز ربات: {bot_score}\n\n"
            f"👤 حالا خودت بولینگ بنداز!"
        )

        context.user_data["game"] = "bowling"
        context.user_data["bet"] = bet
        context.user_data["bot_score"] = bot_score


async def handle_game_result(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    user_id = update.effective_user.id

    game = context.user_data.get("game")

    if not game:
        return

    bet = context.user_data.get("bet")
    bot_score = context.user_data.get("
