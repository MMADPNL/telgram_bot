import json
import os

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    filters,
)

# ==================================================
# تنظیمات
# ==================================================

BOT_TOKEN = "8641446932:AAHoge84NaLhWEE1yCprLh32Wwzn0l1oB2Y"


OWNER_ID = 8552447077

CHANNEL_USERNAME = "@MMAD_KING1W"
GROUP_USERNAME = "@gap_bazi12"

CHANNEL_LINK = "https://t.me/MMAD_KING1W"
GROUP_LINK = "https://t.me/gap_bazi12"

BALANCE_FILE = "balances.json"
OWNER_FILE = "owner.json"

# موجودی اولیه کاربران جدید
START_BALANCE = 0

# حداقل شرط
MIN_BET = 100


# ==================================================
# مدیریت موجودی
# ==================================================

def load_balances():
    if not os.path.exists(BALANCE_FILE):
        return {}

    try:
        with open(BALANCE_FILE, "r", encoding="utf-8") as file:
            return json.load(file)
    except Exception:
        return {}


def save_balances(data):
    with open(BALANCE_FILE, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def get_balance(user_id):
    data = load_balances()
    uid = str(user_id)

    if uid not in data:
        data[uid] = START_BALANCE
        save_balances(data)

    return int(data[uid])


def set_balance(user_id, amount):
    data = load_balances()
    data[str(user_id)] = int(amount)
    save_balances(data)


def add_balance(user_id, amount):
    set_balance(
        user_id,
        get_balance(user_id) + int(amount)
    )


# ==================================================
# مدیریت مالک
# ==================================================

def save_owner(user_id):
    with open(OWNER_FILE, "w", encoding="utf-8") as file:
        json.dump(
            {"owner_id": int(user_id)},
            file,
            ensure_ascii=False,
            indent=2
        )


def load_owner():
    if not os.path.exists(OWNER_FILE):
        save_owner(OWNER_ID)
        return OWNER_ID

    try:
        with open(OWNER_FILE, "r", encoding="utf-8") as file:
            data = json.load(file)

        return int(data["owner_id"])

    except Exception:
        save_owner(OWNER_ID)
        return OWNER_ID


def is_owner(user_id):
    return int(user_id) == load_owner()


# ==================================================
# عضویت اجباری
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

    except Exception as error:
        print("Membership error:", error)
        return False

    valid_statuses = [
        "member",
        "administrator",
        "creator"
    ]

    return (
        channel_member.status in valid_statuses
        and
        group_member.status in valid_statuses
    )


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

    # مالک نیاز به عضویت اجباری ندارد
    if is_owner(user_id):
        return True

    if await check_membership(
        context.bot,
        user_id
    ):
        return True

    text = (
        "🚫 دسترسی بسته است.\n\n"
        "برای استفاده از ربات باید عضو کانال و گپ باشید.\n\n"
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
# منوی اصلی
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
        ]
    ])


# ==================================================
# START
# ==================================================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not await require_membership(update, context):
        return

    user = update.effective_user
    balance = get_balance(user.id)

    await update.message.reply_text(

        f"سلام {user.first_name} 👋\n\n"
        "🤖 به ربات بازی خوش آمدی.\n\n"
        f"🆔 آیدی عددی شما:\n{user.id}\n\n"
        f"💰 موجودی:\n{balance:,} امتیاز\n\n"
        "👇 از منوی زیر انتخاب کن:",

        reply_markup=main_keyboard()
    )


# ==================================================
# ریست موجودی همه کاربران - فقط مالک
# ==================================================

async def reset_balance(update, context):

    user_id = update.effective_user.id

    if not is_owner(user_id):

        await update.message.reply_text(
            "❌ فقط مالک می‌تواند موجودی‌ها را ریست کند."
        )

        return

    data = load_balances()

    for uid in data:
        data[uid] = 0

    save_balances(data)

    await update.message.reply_text(

        "✅ ریست موجودی انجام شد.\n\n"
        f"👥 تعداد کاربران: {len(data)}\n"
        "💰 موجودی همه کاربران: 0"
    )


# ==================================================
# دکمه‌ها
# ==================================================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    # بررسی عضویت
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
                "✅ عضویت شما تأیید شد.\n\n"
                "حالا می‌تونی از ربات استفاده کنی.",
                reply_markup=main_keyboard()
            )

        else:

            await query.message.reply_text(
                "❌ هنوز عضو کانال و گپ نیستی.",
                reply_markup=membership_keyboard()
            )

        return

    # عضویت اجباری
    if not await require_membership(update, context):
        return

    # ==================================================
    # موجودی
    # ==================================================

    if query.data == "balance":

        await query.message.reply_text(

            "💳 موجودی شما:\n\n"
            f"💰 {get_balance(user_id):,} امتیاز"
        )

        return

    # ==================================================
    # دارت
    # ==================================================

    if query.data == "dart":

        context.user_data.clear()
        context.user_data["state"] = "dart_color"

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "⚪ سفید",
                    callback_data="dart_white"
                ),
                InlineKeyboardButton(
                    "🔴 قرمز",
                    callback_data="dart_red"
                )
            ]
        ])

        await query.message.reply_text(
            "🎯 بازی دارت\n\n"
            "اول رنگ موردنظر را انتخاب کن:",
            reply_markup=keyboard
        )

        return

    # انتخاب رنگ دارت
    if query.data in [
        "
