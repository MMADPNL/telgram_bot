import json
import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)


# ==================================================
# SETTINGS
# ==================================================

BOT_TOKEN = "8641446932:AAHoge84NaLhWEE1yCprLh32Wwzn0l1oB2Y"

OWNER_ID = 8552447077

CHANNEL_USERNAME = "@MMAD_KING1W"
GROUP_USERNAME = "@gap_bazi12"

CHANNEL_LINK = "https://t.me/MMAD_KING1W"
GROUP_LINK = "https://t.me/gap_bazi12"

BALANCE_FILE = "balances.json"
OWNER_FILE = "owner.json"

START_POINTS = 0


# ==================================================
# FILE FUNCTIONS
# ==================================================

def load_json(filename, default):
    if not os.path.exists(filename):
        return default

    try:
        with open(filename, "r", encoding="utf-8") as file:
            data = json.load(file)

        return data

    except Exception as e:
        print(f"LOAD ERROR {filename}:", e)
        return default


def save_json(filename, data):
    try:
        with open(filename, "w", encoding="utf-8") as file:
            json.dump(
                data,
                file,
                ensure_ascii=False,
                indent=2
            )

        return True

    except Exception as e:
        print(f"SAVE ERROR {filename}:", e)
        return False


# ==================================================
# POINTS
# ==================================================

def get_points(user_id):
    data = load_json(BALANCE_FILE, {})

    if not isinstance(data, dict):
        data = {}

    uid = str(user_id)

    if uid not in data:
        data[uid] = START_POINTS
        save_json(BALANCE_FILE, data)

    try:
        return int(data[uid])

    except (ValueError, TypeError):
        data[uid] = START_POINTS
        save_json(BALANCE_FILE, data)
        return START_POINTS


def set_points(user_id, amount):
    data = load_json(BALANCE_FILE, {})

    if not isinstance(data, dict):
        data = {}

    data[str(user_id)] = max(0, int(amount))

    save_json(
        BALANCE_FILE,
        data
    )


def add_points(user_id, amount):
    current = get_points(user_id)

    new_amount = current + int(amount)

    if new_amount < 0:
        new_amount = 0

    set_points(
        user_id,
        new_amount
    )

    return new_amount


# ==================================================
# OWNER
# ==================================================

def load_owner():
    if not os.path.exists(OWNER_FILE):

        save_json(
            OWNER_FILE,
            {
                "owner_id": OWNER_ID
            }
        )

        return OWNER_ID

    data = load_json(
        OWNER_FILE,
        {
            "owner_id": OWNER_ID
        }
    )

    try:
        return int(data["owner_id"])

    except Exception:
        save_json(
            OWNER_FILE,
            {
                "owner_id": OWNER_ID
            }
        )

        return OWNER_ID


def save_owner(user_id):
    save_json(
        OWNER_FILE,
        {
            "owner_id": int(user_id)
        }
    )


def is_owner(user_id):
    return int(user_id) == load_owner()


# ==================================================
# MEMBERSHIP
# ==================================================

async def check_membership(bot, user_id):

    try:

        channel = await bot.get_chat_member(
            CHANNEL_USERNAME,
            user_id
        )

        group = await bot.get_chat_member(
            GROUP_USERNAME,
            user_id
        )

        valid = {
            "member",
            "administrator",
            "creator"
        }

        return (
            channel.status in valid
            and
            group.status in valid
        )

    except Exception as e:

        print(
            "MEMBERSHIP ERROR:",
            e
        )

        return False


def membership_keyboard():

    return InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "📢 کانال",
                url=CHANNEL_LINK
            )
        ],

        [
            InlineKeyboardButton(
                "💬 گپ",
                url=GROUP_LINK
            )
        ],

        [
            InlineKeyboardButton(
                "✅ عضو شدم",
                callback_data="check_membership"
            )
        ]

    ])


async def require_membership(
    update,
    context
):

    user_id = update.effective_user.id

    # مالک نیازی به عضویت اجباری ندارد
    if is_owner(user_id):
        return True

    if await check_membership(
        context.bot,
        user_id
    ):
        return True

    text = (
        "🚫 دسترسی بسته است.\n\n"
        "برای استفاده از ربات ابتدا عضو این دو مورد شو:\n\n"
        "📢 کانال\n"
        "💬 گپ\n\n"
        "بعد روی «✅ عضو شدم» بزن."
    )

    if update.callback_query:

        await update.callback_query.message.reply_text(
            text,
            reply_markup=membership_keyboard()
        )

    elif update.message:

        await update.message.reply_text(
            text,
            reply_markup=membership_keyboard()
        )

    return False


# ==================================================
# MAIN MENU
# ==================================================

def main_keyboard(user_id):

    buttons = [

        [
            InlineKeyboardButton(
                "🎯 دارت",
                callback_data="dart"
            ),

            InlineKeyboardButton(
                "🎲 تاس",
                callback_data="dice"
            )
        ],

        [
            InlineKeyboardButton(
                "💳 امتیاز من",
                callback_data="balance"
            )
        ]

    ]

    # فقط مالک
    if is_owner(user_id):

        buttons.extend([

            [
                InlineKeyboardButton(
                    "➕ شارژ امتیاز",
                    callback_data="charge"
                )
            ],

            [
                InlineKeyboardButton(
                    "🔄 ریست امتیازها",
                    callback_data="reset"
                )
            ],

            [
                InlineKeyboardButton(
                    "👑 انتقال مالکیت",
                    callback_data="transfer_owner"
                )
            ]

        ])

    return InlineKeyboardMarkup(buttons)


# ==================================================
# START
# ==================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    if not await require_membership(
        update,
        context
    ):
        return

    user = update.effective_user

    points = get_points(user.id)

    await update.message.reply_text(

        f"سلام {user.first_name} 👋\n\n"

        "🤖 به ربات خوش آمدی.\n\n"

        f"🆔 آیدی:\n{user.id}\n\n"

        f"💰 امتیاز:\n{points:,}\n\n"

        "🎮 یک بازی انتخاب کن:",

        reply_markup=main_keyboard(
            user.id
        )
    )


# ==================================================
# BUTTON HANDLER
# ==================================================

async def button_handler(
    update,
    context
):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    # ==================================================
    # MEMBERSHIP CHECK
    # ==================================================

    if query.data == "check_membership":

        if (
            is_owner(user_id)
            or
            await check_membership(
                context.bot,
                user_id
            )
        ):

            await query.message.reply_text(

                "✅ عضویت تأیید شد.\n\n"
                "🎮 حالا می‌تونی بازی کنی.",

                reply_markup=main_keyboard(
                    user_id
                )
            )

        else:

            await query.message.reply_text(
                "❌ هنوز عضو هر دو مورد نیستی.",
                reply_markup=membership_keyboard()
            )

        return

    # ==================================================
    # MEMBERSHIP
    # ==================================================

    if not await require_membership(
        update,
        context
    ):
        return

    # ==================================================
    # BALANCE
    # ==================================================

    if query.data == "balance":

        points = get_points(user_id)

        await query.message.reply_text(

            "💳 امتیاز شما:\n\n"
            f"💰 {points:,}"

        )

        return

    # ==================================================
    # RESET
    # ==================================================

    if query.data == "reset":

        if not is_owner(user_id):

            await query.message.reply_text(
                "❌ فقط مالک می‌تواند امتیازها را ریست کند."
            )

            return

        save_json(
            BALANCE_FILE,
            {}
        )

        await query.message.reply_text(

            "✅ ریست انجام شد.\n\n"
            "💰 امتیاز تمام کاربران صفر شد."

        )

        return

    # ==================================================
    # DART
    # ==================================================

    if query.data == "dart":

        context.user_data.clear()

        context.user_data["game"] = "dart"

        await query.message.reply_text(

            "🎯 بازی دارت\n\n"
            "🎯 روی دکمه زیر بزن تا دارت پرتاب شود.",

            reply_markup=InlineKeyboardMarkup([

                [
                    InlineKeyboardButton(
                        "🎯 پرتاب دارت",
                        callback_data="throw_dart"
                    )
                ]

            ])
        )

        return

    # ==================================================
    # THROW DART
    # ==================================================

    if query.data == "throw_dart":

        if context.user_data.get("game") != "dart":

            await query.message.reply_text(
                "❌ این بازی فعال نیست."
            )

            return

        try:

            result = await context.bot.send_dice(
                chat_id=query.message.chat_id,
                emoji="🎯"
            )

            value = result.dice.value

        except Exception as e:

            print(
                "DART ERROR:",
                e
            )

            await query.message.reply_text(
                "❌ خطا در اجرای دارت."
            )

            return

        # امتیاز دارت
        points = value * 10

        new_points = add_points(
            user_id,
            points
        )

        await query.message.reply_text(

            "🎯 نتیجه دارت\n\n"

            f"🔢 عدد: {value}\n"
            f"➕ امتیاز: {points:,}\n\n"
            f"💰 امتیاز فعلی: {new_points:,}",

            reply_markup=main_keyboard(
                user_id
            )
        )

        context.user_data.clear()

        return

    # ==================================================
    # DICE
    # ==================================================

    if query.data == "dice":

        context.user_data.clear()

        context.user_data["game"] = "dice"

        await query.message.reply_text(

            "🎲 بازی تاس\n\n"
            "🎲 روی دکمه زیر بزن تا تاس انداخته شود.",

            reply_markup=InlineKeyboardMarkup([

                [
                    InlineKeyboardButton(
                        "🎲 انداختن تاس",
                        callback_data="throw_dice"
                    )
                ]

            ])
        )

        return

    # ==================================================
    # THROW DICE
    # ==================================================

    if query.data == "throw_dice":

        if context.user_data.get("game") != "dice":

            await query.message.reply_text(
                "❌ این بازی فعال نیست."
            )

            return

        try:

            result = await context.bot.send_dice(
                chat_id=query.message.chat_id,
                emoji="🎲"
            )

            value = result.dice.value

        except Exception as e:

            print(
                "DICE ERROR:",
                e
            )

            await query.message.reply_text(
                "❌ خطا در اجرای تاس."
            )

            return

        # امتیاز بر اساس عدد تاس
        points = value * 10

        new_points = add_points(
            user_id,
            points
        )

        await query.message.reply_text(

            "🎲 نتیجه تاس\n\n"

            f"🔢 عدد: {value}\n"
            f"➕ امتیاز: {points:,}\n\n"
            f"💰 امتیاز فعلی: {new_points:,}",

            reply_markup=main_keyboard(
                user_id
            )
        )

        context.user_data.clear()

        return

    # ==================================================
    # CHARGE
    # ==================================================

    if query.data == "charge":

        if not is_owner(user_id):

            await query.message.reply_text(
                "❌ فقط مالک می‌تواند امتیاز شارژ کند."
            )

            return

        context.user_data.clear()

        context.user_data["state"] = "charge"

        await query.message.reply_text(

            "➕ شارژ امتیاز\n\n"

            "آیدی کاربر و مقدار را با فاصله بفرست.\n\n"

            "مثال:\n"
            "123456789 5000"

        )

        return

    # ==================================================
    # TRANSFER OWNER
    # ==================================================

    if query.data == "transfer_owner":

        if not is_owner(user_id):

            await query.message.reply_text(
                "❌ فقط مالک اجازه دارد."
            )

            return

        context.user_data.clear()

        context.user_data["state"] = "transfer_owner"

        await query.message.reply_text(

            "👑 انتقال مالکیت\n\n"
            "آیدی عددی مالک جدید را بفرست:"

        )

        return


# ==================================================
# TEXT HANDLER
# ==================================================

async def text_handler(
    update,
    context
):

    if not await require_membership(
        update,
        context
    ):
        return

    if not update.message:
        return

    text = update.message.text.strip()

    state = context.user_data.get(
        "state"
    )

    user_id = update.effective_user.id

    # ==================================================
    # CHARGE
    # ==================================================

    if state == "charge":

        if not is_owner(user_id):

            context.user_data.clear()

            await update.message.reply_text(
                "❌ فقط مالک اجازه دارد."
            )

            return

        parts = text.split()

        if len(parts) != 2:

            await update.message.reply_text(

                "❌ فرمت اشتباه است.\n\n"
                "مثال:\n"
                "123456789 5000"

            )

            return

        try:

            target_id = int(parts[0])
            amount = int(parts[1])

        except ValueError:

            await update.message.reply_text(
                "❌ هر دو مقدار باید عدد باشند."
            )

            return

        if target_id <= 0 or amount <= 0:

            await update.message.reply_text(
                "❌ مقدار واردشده معتبر نیست."
            )

            return

        new_points = add_points(
            target_id,
            amount
        )

        context.user_data.clear()

        await update.message.reply_text(

            "✅ امتیاز شارژ شد.\n\n"

            f"👤 آیدی: {target_id}\n"
            f"➕ مقدار: {amount:,}\n"
            f"💰 امتیاز جدید: {new_points:,}"

        )

        return

    # ==================================================
    # TRANSFER OWNER
    # ==================================================

    if state == "transfer_owner":

        if not is_owner(user_id):

            context.user_data.clear()

            await update.message.reply_text(
                "❌ فقط مالک اجازه دارد."
            )

            return

        try:

            new_owner = int(text)

        except ValueError:

            await update.message.reply_text(
                "❌ آیدی باید عددی باشد."
            )

            return

        if new_owner <= 0:

            await update.message.reply_text(
                "❌ آیدی معتبر نیست."
            )

            return

        save_owner(
            new_owner
        )

        context.user_data.clear()

        await update.message.reply_text(

            "✅ انتقال مالکیت انجام شد.\n\n"
            f"👑 مالک جدید:\n{new_owner}"

        )

        return


# ==================================================
# BALANCE COMMAND
# ==================================================

async def balance_command(
    update,
    context
):

    if not await require_membership(
        update,
        context
    ):
        return

    user_id = update.effective_user.id

    points = get_points(
        user_id
    )

    await update.message.reply_text(

        "💳 امتیاز شما:\n\n"
        f"💰 {points:,}"

    )


# ==================================================
# MAIN
# ==================================================

def main():

    if BOT_TOKEN == "توکن_ربات_اینجا":

        print(
            "❌ اول BOT_TOKEN را وارد کن."
        )

        return

    app = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    # Commands
    app.add_handler(
        CommandHandler(
            "start",
            start
        )
    )

    app.add_handler(
        CommandHandler(
            "balance",
            balance_command
        )
    )

    # Buttons
    app.add_handler(
        CallbackQueryHandler(
            button_handler
        )
    )

    # Text
    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            text_handler
        )
    )

    print(
        "🤖 Bot is running..."
    )

    app.run_polling(
        drop_pending_updates=True
    )


# ==================================================
# RUN
# ==================================================

if __name__ == "__main__":
    main()
