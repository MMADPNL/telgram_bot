import os

from telegram import Update, ReplyKeyboardMarkup, ReplyKeyboardRemove
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    filters,
)

TOKEN = os.getenv("BOT_TOKEN")

# آیدی صاحب ربات
MY_ID = 8552447077

# موجودی اولیه
MY_START_COINS = 100_000
USER_START_COINS = 1_000

# حداقل و حداکثر شرط
MIN_BET = 100
MAX_BET = 10_000

# موجودی‌ها
coins = {}


def get_coins(user_id):
    if user_id not in coins:
        if user_id == MY_ID:
            coins[user_id] = MY_START_COINS
        else:
            coins[user_id] = USER_START_COINS

    return coins[user_id]


# -------------------------
# شروع ربات
# -------------------------

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id

    keyboard = [
        ["🎲 تاس", "⚽ فوتبال"],
        ["🎳 بولینگ", "💰 سکه"],
    ]

    await update.message.reply_text(
        "🤖 ربات بازی آماده است!\n\n"
        f"🪙 موجودی شما: {get_coins(user_id):,}\n\n"
        "🎲 بازی تاس:\n"
        "1تاس 100\n\n"
        "🎳 بازی بولینگ:\n"
        "1بولینگ 100\n\n"
        "💸 انتقال سکه:\n"
        "روی پیام شخص ریپلای کن و بنویس:\n"
        "انتقال 500\n\n"
        "💰 دیدن موجودی:\n"
        "/coins\n\n"
        "حداقل شرط: 100 🪙\n"
        "حداکثر شرط: 10,000 🪙",
        reply_markup=ReplyKeyboardMarkup(
            keyboard,
            resize_keyboard=True
        )
    )


# -------------------------
# موجودی
# -------------------------

async def coins_command(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    user_id = update.effective_user.id

    await update.message.reply_text(
        f"💰 موجودی شما:\n\n"
        f"🪙 {get_coins(user_id):,} سکه"
    )


# -------------------------
# شارژ فقط صاحب ربات
# -------------------------

async def charge_coins(update: Update, amount: int):
    user_id = update.effective_user.id

    if user_id != MY_ID:
        await update.message.reply_text(
            "❌ این دستور فقط برای صاحب ربات است."
        )
        return

    if amount <= 0:
        await update.message.reply_text(
            "❌ مبلغ باید بیشتر از صفر باشد."
        )
        return

    coins[user_id] = get_coins(user_id) + amount

    await update.message.reply_text(
        f"✅ شارژ انجام شد!\n\n"
        f"➕ مبلغ: {amount:,} 🪙\n"
        f"💰 موجودی جدید: {coins[user_id]:,} 🪙"
    )


# -------------------------
# انتقال سکه
# -------------------------

async def transfer_coins(update: Update, amount: int):
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
        await message.reply_text(
            "❌ نمی‌توانی به ربات سکه بدهی."
        )
        return

    receiver_id = receiver.id

    if sender_id == receiver_id:
        await message.reply_text(
            "❌ نمی‌توانی به خودت سکه انتقال بدهی."
        )
        return

    if amount <= 0:
        await message.reply_text(
            "❌ مبلغ باید بیشتر از صفر باشد."
        )
        return

    sender_balance = get_coins(sender_id)

    if sender_balance < amount:
        await message.reply_text(
            f"❌ موجودی کافی نیست.\n\n"
            f"🪙 موجودی شما: {sender_balance:,}\n"
            f"💸 مبلغ: {amount:,}"
        )
        return

    receiver_balance = get_coins(receiver_id)

    coins[sender_id] = sender_balance - amount
    coins[receiver_id] = receiver_balance + amount

    await message.reply_text(
        f"✅ انتقال انجام شد!\n\n"
        f"👤 گیرنده: {receiver.first_name}\n"
        f"💸 مبلغ: {amount:,} 🪙\n\n"
        f"💰 موجودی شما: {coins[sender_id]:,} 🪙"
    )


# -------------------------
# شروع بازی تاس / بولینگ
# -------------------------

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
            "❌ مبلغ شرط باید عدد باشد.\n\n"
            "مثال:\n"
            "1تاس 100"
        )
        return

    if game not in ["1تاس", "1بولینگ"]:
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
            f"❌ موجودی کافی نیست.\n\n"
            f"🪙 موجودی شما: {balance:,}\n"
            f"💰 شرط: {bet:,}"
        )
        return

    # کم کردن شرط
    coins[user_id] -= bet

    # -------------------------
    # تاس
    # -------------------------

    if game == "1تاس":

        context.user_data["game"] = "dice"
        context.user_data["bet"] = bet

        await update.message.reply_text(
            "🎲 نوبت ربات...\n"
            "ربات در حال انداختن تاس است..."
        )

        # تاس واقعی تلگرام
        dice_message = await update.message.reply_dice(
            emoji="🎲"
        )

        bot_score = dice_message.dice.value

        context.user_data["bot_score"] = bot_score

        keyboard = [
            ["🎲 انداختن تاس من"]
        ]

        await update.message.reply_text(
            f"🤖 نتیجه ربات: {bot_score}\n\n"
            "👤 حالا نوبت توئه!\n"
            "روی دکمه زیر بزن تا تاس خودت انداخته بشه.",
            reply_markup=ReplyKeyboardMarkup(
                keyboard,
                resize_keyboard=True,
                one_time_keyboard=True
            )
        )

        return

    # -------------------------
    # بولینگ
    # -------------------------

    if game == "1بولینگ":

        context.user_data["game"] = "bowling"
        context.user_data["bet"] = bet

        await update.message.reply_text(
            "🎳 نوبت ربات...\n"
            "ربات در حال انداختن بولینگ است..."
        )

        # بولینگ واقعی تلگرام
        bowling_message = await update.message.reply_dice(
            emoji="🎳"
        )

        bot_score = bowling_message.dice.value

        context.user_data["bot_score"] = bot_score

        keyboard = [
            ["🎳 انداختن بولینگ من"]
        ]

        await update.message.reply_text(
            f"🤖 نتیجه ربات: {bot_score}\n\n"
            "👤 حالا نوبت توئه!\n"
            "روی دکمه زیر بزن تا بولینگ خودت انداخته بشه.",
            reply_markup=ReplyKeyboardMarkup(
                keyboard,
                resize_keyboard=True,
                one_time_keyboard=True
            )
        )

        return


# -------------------------
# انداختن تاس / بولینگ کاربر
# -------------------------

async def player_roll(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    user_id = update.effective_user.id
    text = update.message.text.strip()

    game = context.user_data.get("game")

    if not game:
        return

    bet = context.user_data.get("bet")
    bot_score = context.user_data.get("bot_score")

    # -------------------------
    # تاس کاربر
    # -------------------------

    if game == "dice" and text == "🎲 انداختن تاس من":

        await update.message.reply_text(
            "🎲 نوبت تو..."
        )

        player_message = await update.message.reply_dice(
            emoji="🎲"
        )

        player_score = player_message.dice.value

        await finish_game(
            update,
            context,
            user_id,
            bot_score,
            player_score,
            bet
        )

        return

    # -------------------------
    # بولینگ کاربر
    # -------------------------

    if game == "bowling" and text == "🎳 انداختن بولینگ من":

        await update.message.reply_text(
            "🎳 نوبت تو..."
        )

        player_message = await update.message.reply_dice(
            emoji="🎳"
        )

        player_score = player_message.dice.value

        await finish_game(
            update,
            context,
            user_id,
            bot_score,
            player_score,
            bet
        )

        return


# -------------------------
# پایان بازی
# -------------------------

async def finish_game(
    update,
    context,
    user_id,
    bot_score,
    player_score,
    bet
):

    if player_score > bot_score:

        prize = bet * 2

        coins[user_id] = get_coins(user_id) + prize

        result = (
            "🏆 برنده شدی!\n\n"
            f"🪙 جایزه: {prize:,}"
        )

    elif player_score < bot_score:

        result = (
            "😢 باختی!\n\n"
            f"🪙 شرط از دست رفت: {bet:,}"
        )

    else:

        coins[user_id] = get_coins(user_id) + bet

        result = (
            "🤝 مساوی شد!\n\n"
            f"🪙 شرط {bet:,} برگشت داده شد."
        )

    await update.message.reply_text(
        f"🤖 نتیجه ربات: {bot_score}\n"
        f"👤 نتیجه تو: {player_score}\n\n"
        f"{result}\n\n"
        f"💰 موجودی جدید: "
        f"{get_coins(user_id):,} 🪙",
        reply_markup=ReplyKeyboardRemove()
    )

    context.user_data.clear()


# -------------------------
# دکمه‌های اصلی
# -------------------------

async def button_handler(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    text = update.message.text.strip()
    user_id = update.effective_user.id

    # اگر بازی در حال انجام است
    if context.user_data.get("game"):

        await player_roll(
            update,
            context
        )

        return

    # -------------------------
    # شارژ
    # -------------------------

    if text.startswith("شارژ "):

        parts = text.split()

        if len(parts) != 2:

            await update.message.reply_text(
                "❌ مثال:\n"
                "شارژ 50000"
            )

            return

        try:
            amount = int(parts[1])

        except ValueError:

            await update.message.reply_text(
                "❌ مبلغ باید عدد باشد."
            )

            return

        await charge_coins(
            update,
            amount
        )

        return

    # -------------------------
    # انتقال
    # -------------------------

    if text.startswith("انتقال "):

        parts = text.split()

        if len(parts) != 2:

            await update.message.reply_text(
                "❌ مثال:\n"
                "انتقال 500"
            )

            return

        try:
            amount = int(parts[1])

        except ValueError:

            await update.message.reply_text(
                "❌ مبلغ باید عدد باشد."
            )

            return

        await transfer_coins(
            update,
            amount
        )

        return

    # -------------------------
    # شروع بازی
    # -------------------------

    if text.startswith("1تاس"):

        await start_game(
            update,
            context
        )

        return

    if text.startswith("1بولینگ"):

        await start_game(
            update,
            context
        )

        return

    # -------------------------
    # دکمه تاس
    # -------------------------

    if text == "🎲 تاس":

        await update.message.reply_text(
            "🎲 برای بازی بنویس:\n\n"
            "1تاس 100"
        )

        return

    # -------------------------
    # دکمه بولینگ
    # -------------------------

    if text == "🎳 بولینگ":

        await update.message.reply_text(
            "🎳 برای بازی بنویس:\n\n"
            "1بولینگ 100"
        )

        return

    # -------------------------
    # فوتبال
    # -------------------------

    if text == "⚽ فوتبال":

        await update.message.reply_text(
            "⚽ بازی فوتبال به‌زودی اضافه می‌شود."
        )

        return

    # -------------------------
    # سکه
    # -------------------------

    if text == "💰 سکه":

        await coins_command(
            update,
            context
        )

        return


# -------------------------
# اجرای ربات
# -------------------------

def main():

    if not TOKEN:

        raise RuntimeError(
            "BOT_TOKEN تنظیم نشده است"
        )

    app = (
        Application
        .builder()
        .token(TOKEN)
        .build()
    )

    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    app.add_handler(
        CommandHandler(
            "coins",
            coins_command
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            button_handler
        )
    )

    print("Bot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()
