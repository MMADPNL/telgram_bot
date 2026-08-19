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

# =========================
# تنظیمات
# =========================

BOT_TOKEN = 8790498730:AAFJ1WAmwMSSBFsgrnoxCJQFfm59Wo6I214

OWNER_ID = 8552447077

CHANNEL_USERNAME = "@prmiumfarsi"
CHANNEL_LINK = "https://t.me/prmiumfarsi"

DATA_FILE = "users.json"


# =========================
# دیتابیس JSON
# =========================

def load_data():
    if not os.path.exists(DATA_FILE):
        return {
            "owner_id": OWNER_ID,
            "users": {}
        }

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    except Exception:
        return {
            "owner_id": OWNER_ID,
            "users": {}
        }


def save_data(data):
    with open(DATA_FILE, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )


data = load_data()


# =========================
# کاربر
# =========================

def get_user(user_id):
    uid = str(user_id)

    if uid not in data["users"]:
        data["users"][uid] = {
            "invited": 0,
            "invited_users": [],
            "combo_claimed": False,
            "free_claimed": False,
        }

        save_data(data)

    return data["users"][uid]


def is_owner(user_id):
    return int(user_id) == int(data["owner_id"])


# =========================
# منوی اصلی
# =========================

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
        ],
    ]

    return InlineKeyboardMarkup(keyboard)


# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user = update.effective_user
    user_id = user.id

    get_user(user_id)

    # بررسی لینک دعوت
    if context.args:

        try:

            inviter_id = int(context.args[0])

            if inviter_id != user_id:

                inviter = get_user(inviter_id)

                if str(user_id) not in inviter["invited_users"]:

                    inviter["invited_users"].append(
                        str(user_id)
                    )

                    inviter["invited"] += 1

                    save_data(data)

        except (ValueError, TypeError):
            pass

    text = (
        f"سلام {user.first_name} 👋\n\n"
        "به ربات خوش آمدید ❤️\n\n"
        "از منوی زیر گزینه مورد نظر خودت رو انتخاب کن:"
    )

    await update.message.reply_text(
        text,
        reply_markup=main_menu()
    )


# =========================
# لینک دعوت
# =========================

async def my_link(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    bot = await context.bot.get_me()

    user_id = query.from_user.id

    link = f"https://t.me/{bot.username}?start={user_id}"

    user = get_user(user_id)

    text = (
        "🔗 لینک دعوت اختصاصی شما:\n\n"
        f"{link}\n\n"
        f"👥 تعداد دعوت‌های شما: {user['invited']}\n\n"
        "این لینک را برای دوستانت ارسال کن."
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


# =========================
# اک رایگان
# =========================

async def free_account(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    user = get_user(user_id)

    needed = 2

    invited = user["invited"]

    # قبلاً برداشت شده
    if user["free_claimed"]:

        await query.message.edit_text(
            "❌ شما قبلاً اک رایگان خود را برداشت کرده‌اید."
        )

        return

    # شرایط برداشت
    if invited >= needed:

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
            "تبریک! شما شرایط دریافت اک رایگان را دارید. ✅\n\n"
            "برای ارسال درخواست روی دکمه زیر بزنید."
        )

    else:

        remaining = needed - invited

        bot = await context.bot.get_me()

        link = f"https://t.me/{bot.username}?start={user_id}"

        text = (
            "🎁 اک رایگان\n\n"
            f"👥 تعداد لازم: {needed} نفر\n"
            f"👤 دعوت شده: {invited} نفر\n"
            f"⏳ باقی‌مانده: {remaining} نفر\n\n"
            "🔗 لینک دعوت شما:\n"
            f"{link}\n\n"
            "دو نفر را با لینک بالا وارد ربات کنید."
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


# =========================
# کمبو 100 درصد
# =========================

async def combo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    user = get_user(user_id)

    needed = 1

    invited = user["invited"]

    # قبلاً برداشت شده
    if user["combo_claimed"]:

        await query.message.edit_text(
            "❌ شما قبلاً کمبو 100درصد خود را برداشت کرده‌اید."
        )

        return

    # شرایط برداشت
    if invited >= needed:

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
            "تبریک! شما شرایط دریافت کمبو را دارید. ✅\n\n"
            "برای ارسال درخواست روی دکمه زیر بزنید."
        )

    else:

        bot = await context.bot.get_me()

        link = f"https://t.me/{bot.username}?start={user_id}"

        text = (
            "💯 کمبو 100درصد\n\n"
            "👥 برای دریافت کمبو باید 1 نفر را دعوت کنید.\n\n"
            f"👤 دعوت شده: {invited}/1\n\n"
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


# =========================
# برداشت اک رایگان
# =========================

async def claim_free(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    user = get_user(user_id)

    if user["invited"] < 2:

        await query.message.edit_text(
            "❌ شما هنوز شرایط برداشت را ندارید."
        )

        return

    if user["free_claimed"]:

        await query.message.edit_text(
            "❌ درخواست شما قبلاً ثبت شده است."
        )

        return

    user["free_claimed"] = True

    save_data(data)

    user_info = query.from_user

    message = (
        "🎁 درخواست اک رایگان\n\n"
        f"👤 نام: {user_info.full_name}\n"
        f"🆔 آیدی عددی: {user_id}\n"
        f"🔗 یوزرنیم: "
        f"@{user_info.username if user_info.username else 'ندارد'}\n"
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


# =========================
# برداشت کمبو
# =========================

async def claim_combo(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    user = get_user(user_id)

    if user["invited"] < 1:

        await query.message.edit_text(
            "❌ شما هنوز شرایط برداشت را ندارید."
        )

        return

    if user["combo_claimed"]:

        await query.message.edit_text(
            "❌ درخواست شما قبلاً ثبت شده است."
        )

        return

    user["combo_claimed"] = True

    save_data(data)

    user_info = query.from_user

    message = (
        "💯 درخواست کمبو 100درصد\n\n"
        f"👤 نام: {user_info.full_name}\n"
        f"🆔 آیدی عددی: {user_id}\n"
        f"🔗 یوزرنیم: "
        f"@{user_info.username if user_info.username else 'ندارد'}\n"
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


# =========================
# انتقال مالکیت
# =========================

async def transfer_owner(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id

    if not is_owner(user_id):

        await update.message.reply_text(
            "❌ این دستور فقط برای مالک ربات است."
        )

        return

    context.user_data["waiting_for_new_owner"] = True

    await update.message.reply_text(
        "👑 انتقال مالکیت\n\n"
        "آیدی عددی مالک جدید را ارسال کنید:"
    )


# =========================
# دریافت آیدی مالک جدید
# =========================

async def receive_owner_id(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if not context.user_data.get(
        "waiting_for_new_owner"
    ):
        return

    if not is_owner(
        update.effective_user.id
    ):
        return

    text = update.message.text.strip()

    try:

        new_owner_id = int(text)

    except ValueError:

        await update.message.reply_text(
            "❌ آیدی عددی صحیح نیست.\n\n"
            "مثال:\n"
            "123456789"
        )

        return

    data["owner_id"] = new_owner_id

    save_data(data)

    context.user_data[
        "waiting_for_new_owner"
    ] = False

    await update.message.reply_text(
        "✅ انتقال مالکیت با موفقیت انجام شد.\n\n"
        f"👑 مالک جدید:\n"
        f"{new_owner_id}"
    )


# =========================
# بازگشت
# =========================

async def back(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    await query.message.edit_text(
        "🏠 منوی اصلی\n\n"
        "گزینه مورد نظر خودت رو انتخاب کن:",
        reply_markup=main_menu()
    )


# =========================
# Callback
# =========================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    if query.data == "free_account":

        await free_account(
            update,
            context
        )

    elif query.data == "combo":

        await combo(
            update,
            context
        )

    elif query.data == "my_link":

        await my_link(
            update,
            context
        )

    elif query.data == "claim_free":

        await claim_free(
            update,
            context
        )

    elif query.data == "claim_combo":

        await claim_combo(
            update,
            context
        )

    elif query.data == "back":

        await back(
            update,
            context
        )


# =========================
# خطاها
# =========================

async def error_handler(
    update: object,
    context: ContextTypes.DEFAULT_TYPE
):

    print(
        "ERROR:",
        context.error
    )


# =========================
# اجرای ربات
# =========================

def main():

    if not BOT_TOKEN:

        raise ValueError(
            "BOT_TOKEN تنظیم نشده است."
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
            receive_owner_id
        )
    )

    app.add_error_handler(
        error_handler
    )

    print(
        "Bot is running..."
    )

    app.run_polling()


if __name__ == "__main__":

    main()
