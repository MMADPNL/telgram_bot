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
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)
from telegram.error import TelegramError


# ==================================================
# تنظیمات
# ==================================================

BOT_TOKEN = "8790498730:AAFJ1WAmwMSSBFsgrnoxCJQFfm59Wo6I214"

OWNER_ID = 8552447077

CHANNEL_USERNAME = "@prmiumfarsi"
CHANNEL_LINK = "https://t.me/prmiumfarsi"


# ==================================================
# اطلاعات کاربران
# ==================================================

users = {}

owner_id = OWNER_ID


# ==================================================
# کاربر
# ==================================================

def get_user(user_id):

    uid = str(user_id)

    if uid not in users:

        users[uid] = {
            "invited": 0,
            "invited_users": [],
            "free_claimed": False,
            "combo_claimed": False,
        }

    return users[uid]


def is_owner(user_id):

    return int(user_id) == int(owner_id)


# ==================================================
# بررسی عضویت کانال
# ==================================================

async def is_member(bot, user_id):

    try:

        member = await bot.get_chat_member(
            chat_id=CHANNEL_USERNAME,
            user_id=user_id
        )

        return member.status in [
            "member",
            "administrator",
            "creator"
        ]

    except TelegramError as e:

        print("Membership error:", e)

        return False


# ==================================================
# دکمه عضویت
# ==================================================

def join_channel_keyboard():

    keyboard = [

        [
            InlineKeyboardButton(
                "📢 عضویت در کانال",
                url=CHANNEL_LINK
            )
        ],

        [
            InlineKeyboardButton(
                "✅ بررسی عضویت",
                callback_data="check_join"
            )
        ]

    ]

    return InlineKeyboardMarkup(keyboard)


# ==================================================
# منوی اصلی
# ==================================================

def main_menu():

    keyboard = [

        [
            InlineKeyboardButton(
                "🎁 اک رایگان",
                callback_data="free_account"
            )
        ],

        [
            InlineKeyboardButton(
                "💯 کمبو 100درصد",
                callback_data="combo"
            )
        ],

        [
            InlineKeyboardButton(
                "👥 لینک دعوت من",
                callback_data="my_link"
            )
        ]

    ]

    return InlineKeyboardMarkup(keyboard)


# ==================================================
# START
# ==================================================

async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    user = update.effective_user
    user_id = user.id

    get_user(user_id)

    # ==================================================
    # لینک دعوت
    # ==================================================

    if context.args:

        try:

            inviter_id = int(context.args[0])

            # خودش خودش را دعوت نکند
            if inviter_id != user_id:

                inviter = get_user(inviter_id)

                # فقط یک بار حساب شود
                if str(user_id) not in inviter["invited_users"]:

                    inviter["invited_users"].append(
                        str(user_id)
                    )

                    inviter["invited"] += 1

                    # پیام به دعوت کننده
                    try:

                        await context.bot.send_message(

                            chat_id=inviter_id,

                            text=(
                                "🎉 دعوت جدید!\n\n"
                                f"👤 کاربر با آیدی عددی:\n"
                                f"{user_id}\n\n"
                                "به عنوان زیرمجموعه شما ثبت شد ✅️\n\n"
                                f"👥 تعداد کل دعوت‌های شما: "
                                f"{inviter['invited']}"
                            )

                        )

                    except TelegramError as e:

                        print(
                            "INVITER MESSAGE ERROR:",
                            e
                        )

                    print(
                        f"INVITE: {inviter_id} invited {user_id}"
                    )

        except (ValueError, TypeError):

            pass

    # ==================================================
    # بررسی عضویت
    # ==================================================

    member = await is_member(
        context.bot,
        user_id
    )

    if not member:

        await update.message.reply_text(

            "🔒 برای استفاده از ربات ابتدا باید عضو کانال شوید.\n\n"
            "1️⃣ روی «📢 عضویت در کانال» بزنید.\n"
            "2️⃣ عضو کانال شوید.\n"
            "3️⃣ سپس روی «✅ بررسی عضویت» بزنید.",

            reply_markup=join_channel_keyboard()
        )

        return

    # ==================================================
    # ورود به ربات
    # ==================================================

    await update.message.reply_text(

        f"سلام {user.first_name} 👋\n\n"
        "به ربات خوش آمدید ❤️\n\n"
        "از منوی زیر گزینه مورد نظر خودت رو انتخاب کن:",

        reply_markup=main_menu()
    )


# ==================================================
# بررسی عضویت
# ==================================================

async def check_join(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    member = await is_member(
        context.bot,
        user_id
    )

    if not member:

        await query.answer(
            "❌ هنوز عضو کانال نشده‌ای!",
            show_alert=True
        )

        return

    await query.message.edit_text(

        "✅ عضویت شما تأیید شد.\n\n"
        "🎉 حالا می‌توانید از ربات استفاده کنید.",

        reply_markup=main_menu()
    )


# ==================================================
# لینک دعوت
# ==================================================

async def my_link(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    user = get_user(user_id)

    bot = await context.bot.get_me()

    link = (
        f"https://t.me/{bot.username}"
        f"?start={user_id}"
    )

    text = (

        "🔗 لینک دعوت اختصاصی شما\n\n"

        f"{link}\n\n"

        f"👥 تعداد دعوت‌ها: "
        f"{user['invited']}\n\n"

        "لینک را برای دوستانت بفرست."
    )

    keyboard = [

        [
            InlineKeyboardButton(
                "🔙 بازگشت",
                callback_data="back"
            )
        ]

    ]

    await query.message.edit_text(

        text,

        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )


# ==================================================
# اک رایگان
# ==================================================

async def free_account(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    # بررسی عضویت
    if not await is_member(
        context.bot,
        user_id
    ):

        await query.message.edit_text(

            "🔒 ابتدا باید عضو کانال شوید.",

            reply_markup=join_channel_keyboard()
        )

        return

    user = get_user(user_id)

    needed = 2

    if user["free_claimed"]:

        await query.message.edit_text(

            "❌ شما قبلاً اک رایگان خود را برداشت کرده‌اید.",

            reply_markup=main_menu()
        )

        return

    # ==================================================
    # شرایط دریافت
    # ==================================================

    if user["invited"] >= needed:

        keyboard = [

            [
                InlineKeyboardButton(
                    "✅ برداشت",
                    callback_data="claim_free"
                )
            ],

            [
                InlineKeyboardButton(
                    "🔙 بازگشت",
                    callback_data="back"
                )
            ]

        ]

        text = (

            "🎁 اک رایگان\n\n"

            "تبریک! شرایط دریافت اک رایگان را دارید. ✅\n\n"

            "برای ارسال درخواست روی «برداشت» بزنید."
        )

    else:

        bot = await context.bot.get_me()

        link = (
            f"https://t.me/{bot.username}"
            f"?start={user_id}"
        )

        remaining = needed - user["invited"]

text = (
    "🎁 اک رایگان\n\n"
    f"👥 تعداد لازم: {needed} نفر\n"
    f"👤 دعوت شده: {user['invited']} نفر\n"
    f"⏳ باقی‌مانده: {remaining} نفر\n\n"
    "🔗 لینک دعوت شما:\n"
    f"{link}\n\n"
    "دو نفر را با لینک بالا وارد ربات کنید."
)
