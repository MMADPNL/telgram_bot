import json
import os

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)

from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
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

START_BALANCE = 0

MIN_BET = 100


# ==================================================
# BALANCES
# ==================================================

def load_balances():
    if not os.path.exists(BALANCE_FILE):
        return {}

    try:
        with open(
            BALANCE_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        if not isinstance(data, dict):
            return {}

        return data

    except Exception as e:

        print("BALANCE LOAD ERROR:", e)

        return {}


def save_balances(data):

    with open(
        BALANCE_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )


def get_balance(user_id):

    data = load_balances()

    uid = str(user_id)

    if uid not in data:

        data[uid] = START_BALANCE

        save_balances(data)

    try:

        return int(data[uid])

    except Exception:

        data[uid] = START_BALANCE

        save_balances(data)

        return START_BALANCE


def set_balance(user_id, amount):

    data = load_balances()

    data[str(user_id)] = int(amount)

    save_balances(data)


def add_balance(user_id, amount):

    current = get_balance(user_id)

    set_balance(
        user_id,
        current + int(amount)
    )


# ==================================================
# OWNER
# ==================================================

def save_owner(user_id):

    with open(
        OWNER_FILE,
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            {
                "owner_id": int(user_id)
            },
            f,
            ensure_ascii=False,
            indent=2
        )


def load_owner():

    if not os.path.exists(OWNER_FILE):

        save_owner(OWNER_ID)

        return int(OWNER_ID)

    try:

        with open(
            OWNER_FILE,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

        return int(data["owner_id"])

    except Exception as e:

        print("OWNER LOAD ERROR:", e)

        save_owner(OWNER_ID)

        return int(OWNER_ID)


def is_owner(user_id):

    return int(user_id) == load_owner()


# ==================================================
# MEMBERSHIP
# ==================================================

async def check_membership(bot, user_id):

    try:

        channel_member = await bot.get_chat_member(
            CHANNEL_USERNAME,
            user_id
        )

        group_member = await bot.get_chat_member(
            GROUP_USERNAME,
            user_id
        )

        valid_statuses = [
            "member",
            "administrator",
            "creator"
        ]

        channel_ok = (
            channel_member.status
            in valid_statuses
        )

        group_ok = (
            group_member.status
            in valid_statuses
        )

        return channel_ok and group_ok

    except Exception as e:

        print("MEMBERSHIP ERROR:", e)

        return False


def membership_keyboard():

    return InlineKeyboardMarkup([

        [
            InlineKeyboardButton(
                "📢 عضویت در کانال",
                url=CHANNEL_LINK
            )
        ],

        [
            InlineKeyboardButton(
                "💬 عضویت در گپ",
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


async def require_membership(update, context):

    user_id = update.effective_user.id

    # مالک از عضویت اجباری مستثنی است
    if is_owner(user_id):
        return True

    if await check_membership(
        context.bot,
        user_id
    ):

        return True

    text = (
        "🚫 دسترسی بسته است.\n\n"
        "برای استفاده از ربات باید عضو هر دو مورد زیر باشید:\n\n"
        "📢 کانال\n"
        "💬 گپ\n\n"
        "بعد از عضویت روی «✅ عضو شدم» بزن."
    )

    if update.callback_query:

        await update.callback_query.message.reply_text(
            text,
            reply_markup=membership_keyboard()
        )

    else:

        await update.message.reply_text(
            text,
            reply_markup=membership_keyboard()
        )

    return False


# ==================================================
# MAIN KEYBOARD
# ==================================================

def main_keyboard():

    return InlineKeyboardMarkup([

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
                "💸 برداشت",
                callback_data="withdraw"
            )
        ],

        [
            InlineKeyboardButton(
                "👑 انتقال مالکیت",
                callback_data="transfer_owner"
            )
        ],

        [
            InlineKeyboardButton(
                "💰 شارژ موجودی",
                callback_data="charge"
            )
        ],

        [
            InlineKeyboardButton(
                "💳 موجودی",
                callback_data="balance"
            )
        ],

        [
            InlineKeyboardButton(
                "🔄 ریست موجودی",
                callback_data="reset_balance"
            )
        ]

    ])


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

    balance = get_balance(user.id)

    await update.message.reply_text(

        f"سلام {user.first_name} 👋\n\n"

        "🤖 به ربات خوش آمدی.\n\n"

        f"🆔 آیدی عددی:\n{user.id}\n\n"

        f"💰 موجودی:\n{balance:,}\n\n"

        "👇 از منوی زیر انتخاب کن:",

        reply_markup=main_keyboard()
    )


# ==================================================
# RESET BALANCE
# ==================================================

async def reset_balance(
    update,
    context
):

    user_id = update.effective_user.id

    if not is_owner(user_id):

        await update.message.reply_text(
            "❌ فقط مالک می‌تواند موجودی‌ها را ریست کند."
        )

        return

    try:

        save_balances({})

        check = load_balances()

        if check != {}:

            await update.message.reply_text(
                "❌ ریست انجام نشد."
            )

            return

        await update.message.reply_text(

            "✅ ریست با موفقیت انجام شد!\n\n"

            "💰 موجودی تمام کاربران: 0\n"

            "🗑 موجودی‌های قبلی پاک شدند."

        )

            except Exception:
            add_balance(
                user_id,
                amount
            )

            await update.message.reply_text(
                "❌ ارسال درخواست برداشت انجام نشد.\n\n"
                "موجودی شما برگشت داده شد."
            )

            print(
                "WITHDRAW ERROR:",
                e
            )

            return
