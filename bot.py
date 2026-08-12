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

MY_ID = 8552447077

MY_START_COINS = 100_000
USER_START_COINS = 1_000

MIN_BET = 100
MAX_BET = 10_000

coins = {}


def get_coins(user_id):
    if user_id not in coins:
        if user_id == MY_ID:
            coins[user_id] = MY_START_COINS
        else:
            coins[user_id] = USER_START_COINS

    return coins[user_id]


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    await update.message.reply_text(
        f"🤖 ربات بازی آماده است!\n\n"
        f"🪙 موجودی: {get_coins(user_id):,}\n\n"
        "🎲 تاس:\n"
        "1تاس 100\n\n"
        "🎳 بولینگ:\n"
        "1بولینگ 100\n\n"
        "💸 انتقال:\n"
        "روی پیام شخص ریپلای کن و بنویس:\n"
        "انتقال 500\n\n"
        "💰 موجودی:\n"
        "/coins\n\n"
        "حداقل شرط: 100 🪙\n"
        "حداکثر شرط: 10,000 🪙"
    )


async def coins_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    await update.message.reply_text(
        f"💰 موجودی شما:\n"
        f"🪙 {get_coins(user_id):,} سکه"
    )


async def transfer(update: Update, amount):
    sender_id = update.effective_user.id
    message = update.message

    if not message.reply_to_message:
        await message.reply_text(
            "❌ برای انتقال باید روی پیام شخص ریپلای کنی.\n\n"
            "مثال:\n"
            "انتقال 500"
        )
        return

    receiver = message.reply_to_message.from_user

    if receiver.is_bot:
        await message.reply_text("❌ نمی‌توانی به ربات سکه بدهی.")
        return

    receiver_id = receiver.id

    if sender_id == receiver_id:
        await message.reply_text(
            "❌ نمی‌توانی به خودت سکه انتقال بدهی."
        )
        return

    if amount <= 0:
        await message.reply_text(
            "❌ مقدار باید بیشتر از صفر باشد."
        )
        return

    sender_coins = get_coins(sender_id)

    if sender_coins < amount:
        await message.reply_text(
            f"❌ موجودی کافی نیست.\n"
            f"🪙 موجودی شما: {sender_coins:,}"
        )
        return

    receiver_coins = get_coins(receiver_id)

    coins[sender_id] = sender_coins - amount
    coins[receiver_id] = receiver_coins + amount

    await message.reply_text(
        f"✅ انتقال انجام شد!\n\n"
        f"👤 گیرنده: {receiver.first_name}\n"
        f"💸 مبلغ: {amount:,} 🪙\n\n"
        f"💰 موجودی شما: {coins[sender_id]:,} 🪙"
    )


async def start_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    parts = text.split()

    if len(parts) != 2:
        return

    game = parts[0]

    try:
        bet = int(parts[1])
    except ValueError:
        await update.message.reply_text(
            "❌ مبلغ شرط باید عدد باشد.\n"
            "مثال: 1تاس 100"
        )
        return

    if game not in ("1تاس", "1بولینگ"):
        return

    if bet < MIN_BET:
        await update.message.reply_text(
            "❌ حداقل شرط 100 سکه است."
        )
        return

    if bet > MAX_BET:
        await update.message.reply_text(
            "❌ حداکثر شرط 10,000 سکه است."
        )
        return

    balance = get_coins(user_id)

    if balance < bet:
        await update.message.reply_text(
            f"❌ موجودی کافی نیست.\n"
            f"🪙 موجودی شما: {balance:,}"
        )
        return

    coins[user_id] -= bet

    if game == "1تاس":
        bot_score = random.randint(1, 6)

        context.user_data["game"] = "dice"
        context.user_data["bet"] = bet
        context.user_data["bot_score"] = bot_score

        await update.message.reply_text(
            f"🎲 بازی تاس شروع شد!\n\n"
            f"💰 شرط: {bet:,} 🪙\n"
            f"🤖 تاس ربات: {bot_score}\n\n"
            "👤 حالا عدد تاس خودت را بفرست (1 تا 6)."
        )

    else:
        bot_score = random.randint(0, 100)

        context.user_data["game"] = "bowling"
        context.user_data["bet"] = bet
        context.user_data["bot_score"] = bot_score

        await update.message.reply_text(
            f"🎳 بازی بولینگ شروع شد!\n\n"
            f"💰 شرط: {bet:,} 🪙\n"
            f"🤖 امتیاز ربات: {bot_score}\n\n"
            "👤 حالا امتیاز خودت را بفرست (0 تا 100)."
        )


async def game_result(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    game = context.user_data.get("game")

    if not game:
        return False

    bet = context.user_data["bet"]
    bot_score = context.user_data["bot_score"]

    try:
        user_score = int(update.message.text.strip())
    except ValueError:
        return False

    if game == "dice":
        if user_score < 1 or user_score > 6:
            await update.message.reply_text(
                "❌ عدد تاس باید بین 1 تا 6 باشد."
            )
            return True

    if game == "bowling":
        if user_score < 0 or user_score > 100:
            await update.message.reply_text(
                "❌ امتیاز بولینگ باید بین 0 تا 100 باشد."
            )
            return True

    if user_score > bot_score:
        prize = bet * 2
        coins[user_id] += prize

        text = (
            "🏆 بردی!\n"
            f"🪙 جایزه: {prize:,}"
        )

    elif user_score < bot_score:
        text = (
            "😢 باختی!\n"
            f"🪙 شرط: {bet:,}"
        )

    else:
        coins[user_id] += bet

        text = (
            "🤝 مساوی!\n"
            f"🪙 شرط {bet:,} برگشت داده شد."
        )

    await update.message.reply_text(
        f"🤖 نتیجه ربات: {bot_score}\n"
        f"👤 نتیجه تو: {user_score}\n\n"
        f"{text}\n\n"
        f"💰 موجودی جدید: {coins[user_id]:,} 🪙"
    )

    context.user_data.clear()

    return True


async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.effective_user.id

    # نتیجه بازی در حال انجام
    if context.user_data.get("game"):
        if await game_result(update, context):
            return

    # شارژ فقط برای صاحب ربات
    if text.startswith("شارژ "):
        if user_id != MY_ID:
            await update.message.reply_text(
                "❌ این دستور فقط برای صاحب ربات است."
            )
            return

        try:
            amount = int(text.split()[1])
        except (ValueError, IndexError):
            await update.message.reply_text(
                "❌ مثال:\nشارژ 50000"
            )
            return

        if amount <= 0:
            await update.message.reply_text(
                "❌ مبلغ باید بیشتر از صفر باشد."
            )
            return

        coins[user_id] = get_coins(user_id) + amount

        await update.message.reply_text(
            f"✅ {amount:,} سکه اضافه شد.\n\n"
            f"💰 موجودی جدید: {coins[user_id]:,} 🪙"
        )
        return

    # انتقال
    if text.startswith("انتقال "):
        try:
            amount = int(text.split()[1])
            await transfer(update, amount)
        except (ValueError, IndexError):
            await update.message.reply_text(
                "❌ مثال:\nانتقال 500"
            )
        return

    # شروع بازی
    if text.startswith("1تاس") or text.startswith("1بولینگ"):
        await start_game(update, context)
        return

    if text == "🎲 تاس":
        await update.message.reply_text(
            "🎲 مثال:\n1تاس 100"
        )

    elif text == "🎳 بولینگ":
        await update.message.reply_text(
            "🎳 مثال:\n1بولینگ 100"
        )

    elif text == "⚽ فوتبال":
        await update.message.reply_text(
            "⚽ فوتبال فعلاً در حال ساخت است."
        )

    elif text == "💰 سکه":
        await coins_command(update, context)


def main():
    if not TOKEN:
        raise RuntimeError("BOT_TOKEN تنظیم نشده است")

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("coins", coins_command))

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            message_handler
        )
    )

    print("Bot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()
