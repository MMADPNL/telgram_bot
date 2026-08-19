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
    ContextTypes,
)
from telegram.error import TelegramError


# ==================================================
# تنظیمات
# ==================================================

BOT_TOKEN = "8790498730:AAFJ1WAmwMSSBFsgrnoxCJQFfm59Wo6I214"


OWNER_ID = 8552447077

# کانال اجباری
CHANNEL_USERNAME = "@prmiumfarsi"
CHANNEL_LINK = "https://t.me/prmiumfarsi"


# ==================================================
# اطلاعات کاربران
# بدون ساخت users.json
# ==================================================

users = {}

owner_id = OWNER_ID


def get_user(user_id):
    user_id = str(user_id)

    if user_id not in users:
        users[user_id] = {
            "invited": 0,
            "invited_users": [],
            "free_claimed": False,
            "combo_claimed": False,
        }

    return users[user_id]


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
# دکمه عضویت کانال
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

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    user_id = user.id

    get_user(user_id)

    # ----------------------------------------------
    # بررسی لینک دعوت
    # ----------------------------------------------

    if context.args:

        try:

            inviter_id = int(context.args[0])

            # خودش خودش را دعوت نکند
            if inviter_id != user_id:

                inviter = get_user(inviter_id)

                # دعوت فقط یک بار حساب شود
                if str(user_id) not in inviter["invited_users"]:

                    inviter["invited_users"].append(
                        str(user_id)
                    )

                    inviter["invited"] += 1

                    print(
                        f"INVITE: {inviter_id} invited {user_id}"
                    )

        except (ValueError, TypeError):

            pass

    # ----------------------------------------------
    # عضویت کانال
    # ----------------------------------------------

    member = await is_member(
        context.bot,
        user_id
    )

    if not member:

        await update.message.reply_text(
            "🔒 برای استفاده از ربات ابتدا باید عضو کانال شوید.\n\n"
            "بعد از عضویت روی «بررسی عضویت» بزنید.",
            reply_markup=join_channel_keyboard()
        )

        return

    # ----------------------------------------------
    # ورود به ربات
    # ----------------------------------------------

    await update.message.reply_text(
        f"سلام {user.first_name} 👋\n\n"
        "به ربات خوش آمدید ❤️\n\n"
        "از منوی زیر گزینه مورد نظر خودت رو انتخاب کن:",
        reply_markup=main_menu()
    )


# ==================================================
# بررسی عضویت با دکمه
# ==================================================

async def check_join(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    member = await is_member(
        context.bot,
        user_id
    )

    if not member:

        await query.answer(
            "❌ هنوز عضو کانال نشده‌اید.",
            show_alert=True
        )

        return

    await query.message.edit_text(
        "✅ عضویت شما تأیید شد.\n\n"
        "حالا می‌توانید از ربات استفاده کنید.",
        reply_markup=main_menu()
    )


# ==================================================
# لینک دعوت
# ==================================================

async def my_link(update: Update, context: ContextTypes.DEFAULT_TYPE):

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
        f"👥 تعداد دعوت‌ها: {user['invited']}\n\n"
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
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ==================================================
# اک رایگان
# ==================================================

async def free_account(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    # بررسی عضویت
    if not await is_member(context.bot, user_id):

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
            "برای ارسال درخواست روی برداشت بزنید."
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
            f"{link}"
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "👥 لینک دعوت من",
                    callback_data="my_link"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 بازگشت",
                    callback_data="back"
                )
            ]
        ]

    await query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ==================================================
# کمبو
# ==================================================

async def combo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    if not await is_member(context.bot, user_id):

        await query.message.edit_text(
            "🔒 ابتدا باید عضو کانال شوید.",
            reply_markup=join_channel_keyboard()
        )

        return

    user = get_user(user_id)

    needed = 1

    if user["combo_claimed"]:

        await query.message.edit_text(
            "❌ شما قبلاً کمبو 100درصد را برداشت کرده‌اید.",
            reply_markup=main_menu()
        )

        return

    if user["invited"] >= needed:

        keyboard = [
            [
                InlineKeyboardButton(
                    "✅ برداشت",
                    callback_data="claim_combo"
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
            "💯 کمبو 100درصد\n\n"
            "تبریک! شرایط دریافت کمبو را دارید. ✅\n\n"
            "برای ارسال درخواست روی برداشت بزنید."
        )

    else:

        bot = await context.bot.get_me()

        link = (
            f"https://t.me/{bot.username}"
            f"?start={user_id}"
        )

        text = (
            "💯 کمبو 100درصد\n\n"
            "👥 برای دریافت کمبو باید 1 نفر را دعوت کنید.\n\n"
            f"👤 دعوت شده: {user['invited']}/1\n\n"
            "🔗 لینک دعوت شما:\n"
            f"{link}"
        )

        keyboard = [
            [
                InlineKeyboardButton(
                    "👥 لینک دعوت من",
                    callback_data="my_link"
                )
            ],
            [
                InlineKeyboardButton(
                    "🔙 بازگشت",
                    callback_data="back"
                )
            ]
        ]

    await query.message.edit_text(
        text,
        reply_markup=InlineKeyboardMarkup(keyboard)
    )


# ==================================================
# برداشت اک
# ==================================================

async def claim_free(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    user = get_user(user_id)

    if user["invited"] < 2:

        await query.message.edit_text(
            "❌ شما هنوز ۲ نفر دعوت نکرده‌اید.",
            reply_markup=main_menu()
        )

        return

    if user["free_claimed"]:

        await query.message.edit_text(
            "❌ درخواست شما قبلاً ثبت شده است.",
            reply_markup=main_menu()
        )

        return

    user["free_claimed"] = True

    info = query.from_user

    message = (
        "🎁 درخواست اک رایگان\n\n"
        f"👤 نام: {info.full_name}\n"
        f"🆔 آیدی عددی: {user_id}\n"
        f"🔗 یوزرنیم: "
        f"@{info.username if info.username else 'ندارد'}\n"
        f"👥 دعوت‌ها: {user['invited']}\n\n"
        "نوع درخواست: اک رایگان"
    )

    try:

        await context.bot.send_message(
            chat_id=CHANNEL_USERNAME,
            text=message
        )

    except Exception as e:

        print("CHANNEL ERROR:", e)

    await query.message.edit_text(
        "برداشت شما به کانال زیر ارسال شد ✅️\n\n"
        f"{CHANNEL_LINK}"
    )


# ==================================================
# برداشت کمبو
# ==================================================

async def claim_combo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    user = get_user(user_id)

    if user["invited"] < 1:

        await query.message.edit_text(
            "❌ شما هنوز ۱ نفر دعوت نکرده‌اید.",
            reply_markup=main_menu()
        )

        return

    if user["combo_claimed"]:

        await query.message.edit_text(
            "❌ درخواست شما قبلاً ثبت شده است.",
            reply_markup=main_menu()
        )

        return

    user["combo_claimed"] = True

    info = query.from_user

    message = (
        "💯 درخواست کمبو 100درصد\n\n"
        f"👤 نام: {info.full_name}\n"
        f"🆔 آیدی عددی: {user_id}\n"
        f"🔗 یوزرنیم: "
        f"@{info.username if info.username else 'ندارد'}\n"
        f"👥 دعوت‌ها: {user['invited']}\n\n"
        "نوع درخواست: کمبو 100درصد"
    )

    try:

        await context.bot.send_message(
            chat_id=CHANNEL_USERNAME,
            text=message
        )

    except Exception as e:

        print("CHANNEL ERROR:", e)

    await query.message.edit_text(
        "برداشت شما به کانال زیر ارسال شد ✅️\n\n"
        f"{CHANNEL_LINK}"
    )


# ==================================================
# انتقال مالکیت
# ==================================================

async def transfer_owner(update: Update, context: ContextTypes.DEFAULT_TYPE):

    global owner_id

    user_id = update.effective_user.id

    if not is_owner(user_id):

        await update.message.reply_text(
            "❌ این دستور فقط برای مالک ربات است."
        )

        return

    context.user_data["waiting_owner"] = True

    await update.message.reply_text(
        "👑 انتقال مالکیت\n\n"
        "آیدی عددی مالک جدید را ارسال کن:"
    )


# ==================================================
# دریافت آیدی مالک جدید
# ==================================================

async def receive_owner_id(update: Update, context: ContextTypes.DEFAULT_TYPE):

    global owner_id

    if not context.user_data.get("waiting_owner"):

        return

    if not is_owner(update.effective_user.id):

        return

    text = update.message.text.strip()

    try:

        new_owner = int(text)

    except ValueError:

        await update.message.reply_text(
            "❌ آیدی عددی اشتباه است."
        )

        return

    owner_id = new_owner

    context.user_data["waiting_owner"] = False

    await update.message.reply_text(
        "✅ انتقال مالکیت کامل شد.\n\n"
        f"👑 مالک جدید:\n{new_owner}"
    )


# ==================================================
# بازگشت
# ==================================================

async def back(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    await query.message.edit_text(
        "🏠 منوی اصلی",
        reply_markup=main_menu()
    )


# ==================================================
# دکمه‌ها
# ==================================================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    if query.data == "check_join":

        await check_join(update, context)

    elif query.data == "free_account":

        await free_account(update, context)

    elif query.data == "combo":

        await combo(update, context)

    elif query.data == "my_link":

        await my_link(update, context)

    elif query.data == "claim_free":

        await claim_free(update, context)

    elif query.data == "claim_combo":

        await claim_combo(update, context)

    elif query.data == "back":

        await back(update, context)


# ==================================================
# پیام‌های متنی
# ==================================================

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if context.user_data.get("waiting_owner"):

        await receive_owner_id(
            update,
            context
        )


# ==================================================
# خطا
# ==================================================

async def error_handler(update, context):

    print(
        "ERROR:",
        context.error
    )


# ==================================================
# اجرای ربات
# ==================================================

def main():

    if BOT_TOKEN == "توکن_واقعی_ربات_را_اینجا_بگذار":

        raise ValueError(
            "توکن ربات را داخل BOT_TOKEN قرار بده."
        )

    app = (
        Application
        .builder()
        .token(BOT_TOKEN)
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
            "transferowner",
            transfer_owner
        )
    )

    app.add_handler(
        CallbackQueryHandler(
            button_handler
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            text_handler
        )
    )

    app.add_error_handler(
        error_handler
    )

    print("Bot is running...")

    app.run_polling()


if __name__ == "__main__":
    main()
