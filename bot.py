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

# ==================================================
# تنظیمات
# ==================================================

BOT_TOKEN = "8641446932:AAHoge84NaLhWEE1yCprLh32Wwzn0l1oB2Y"

# آیدی عددی خودت
OWNER_ID = 8552447077

CHANNEL_USERNAME = "@MMAD_KING1W"
GROUP_USERNAME = "@gap_bazi12"

CHANNEL_LINK = "https://t.me/MMAD_KING1W"
GROUP_LINK = "https://t.me/gap_bazi12"

BALANCE_FILE = "balances.json"
OWNER_FILE = "owner.json"

# کاربر جدید = صفر
START_BALANCE = 0

# حداقل شرط
MIN_BET = 100


# ==================================================
# موجودی
# ==================================================

def load_balances():
    if not os.path.exists(BALANCE_FILE):
        return {}

    try:
        with open(BALANCE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if not isinstance(data, dict):
            return {}

        return data

    except Exception as e:
        print("BALANCE LOAD ERROR:", e)
        return {}


def save_balances(data):
    with open(BALANCE_FILE, "w", encoding="utf-8") as f:
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
# مالک
# ==================================================

def save_owner(user_id):
    with open(OWNER_FILE, "w", encoding="utf-8") as f:
        json.dump(
            {"owner_id": int(user_id)},
            f,
            ensure_ascii=False,
            indent=2
        )


def load_owner():
    """
    اگر owner.json وجود داشته باشد،
    مالک از آن خوانده می‌شود.
    """

    if not os.path.exists(OWNER_FILE):
        save_owner(OWNER_ID)
        return int(OWNER_ID)

    try:
        with open(OWNER_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        owner = int(data["owner_id"])
        return owner

    except Exception as e:
        print("OWNER LOAD ERROR:", e)

        save_owner(OWNER_ID)
        return int(OWNER_ID)


def is_owner(user_id):
    return int(user_id) == load_owner()


# ==================================================
# بررسی عضویت
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

    # مالک آزاد است
    if is_owner(user_id):
        return True

    if await check_membership(
        context.bot,
        user_id
    ):
        return True

    text = (
        "🚫 دسترسی بسته است.\n\n"
        "ابتدا در کانال و گپ عضو شو:\n\n"
        "📢 کانال\n"
        "💬 گپ\n\n"
        "بعد روی «✅ عضو شدم» بزن."
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
        "👇 یکی از گزینه‌ها را انتخاب کن:",
        reply_markup=main_keyboard()
    )


# ==================================================
# دستور ownerid
# ==================================================

async def ownerid_command(update, context):

    user_id = update.effective_user.id
    registered_owner = load_owner()

    await update.message.reply_text(
        "🔎 اطلاعات مالکیت\n\n"
        f"🆔 آیدی شما:\n{user_id}\n\n"
        f"👑 مالک ثبت‌شده:\n{registered_owner}\n\n"
        f"⚙️ OWNER_ID داخل کد:\n{OWNER_ID}"
    )


# ==================================================
# دستور reset
# ==================================================

async def reset_balance(update, context):

    user_id = update.effective_user.id

    # بررسی مالک
    if not is_owner(user_id):

        await update.message.reply_text(
            "❌ فقط مالک می‌تواند موجودی‌ها را ریست کند.\n\n"
            f"🆔 آیدی شما: {user_id}\n"
            f"👑 مالک فعلی: {load_owner()}"
        )

        return

    try:

        # پاک کردن کامل موجودی‌ها
        save_balances({})

        # بررسی واقعی فایل
        check = load_balances()

        if check != {}:

            await update.message.reply_text(
                "❌ فایل موجودی خالی نشد."
            )

            return

        await update.message.reply_text(
            "✅ ریست با موفقیت انجام شد.\n\n"
            "🗑 تمام موجودی‌های قبلی پاک شدند.\n"
            "💰 موجودی همه کاربران: 0\n\n"
            "کاربران جدید نیز با موجودی 0 ساخته می‌شوند."
        )

    except Exception as e:

        print("RESET ERROR:", e)

        await update.message.reply_text(
            f"❌ خطا در ریست:\n\n{e}"
        )


# ==================================================
# انتقال مالکیت با دستور
# ==================================================

async def transfer_owner_command(update, context):

    user_id = update.effective_user.id

    if not is_owner(user_id):

        await update.message.reply_text(
            "❌ فقط مالک اجازه دارد."
        )

        return

    if len(context.args) != 1:

        await update.message.reply_text(
            "❌ فرمت اشتباه است.\n\n"
            "مثال:\n"
            "/transferowner 123456789"
        )

        return

    try:
        new_owner = int(context.args[0])
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

    save_owner(new_owner)

    await update.message.reply_text(
        "✅ انتقال مالکیت انجام شد.\n\n"
        f"👑 مالک جدید:\n{new_owner}"
    )


# ==================================================
# شارژ با دستور
# ==================================================

async def charge_command(update, context):

    user_id = update.effective_user.id

    if not is_owner(user_id):

        await update.message.reply_text(
            "❌ فقط مالک اجازه دارد."
        )

        return

    if len(context.args) != 2:

        await update.message.reply_text(
            "❌ فرمت اشتباه است.\n\n"
            "مثال:\n"
            "/charge 123456789 50000"
        )

        return

    try:
        target_id = int(context.args[0])
        amount = int(context.args[1])

    except ValueError:

        await update.message.reply_text(
            "❌ آیدی و مقدار باید عدد باشند."
        )

        return

    if target_id <= 0 or amount <= 0:

        await update.message.reply_text(
            "❌ مقدار نامعتبر است."
        )

        return

    add_balance(
        target_id,
        amount
    )

    await update.message.reply_text(
        "✅ شارژ انجام شد.\n\n"
        f"👤 آیدی: {target_id}\n"
        f"💰 مقدار: {amount:,}\n"
        f"💳 موجودی جدید: {get_balance(target_id):,}"
    )


# ==================================================
# BUTTON HANDLER
# ==================================================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    # ------------------------------------------------
    # عضویت
    # ------------------------------------------------

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
                "✅ عضویت تأیید شد.",
                reply_markup=main_keyboard()
            )

        else:

            await query.message.reply_text(
                "❌ هنوز عضو کانال و گپ نیستی.",
                reply_markup=membership_keyboard()
            )

        return

    # ------------------------------------------------
    # اجبار عضویت
    # ------------------------------------------------

    if not await require_membership(
        update,
        context
    ):
        return

    # ------------------------------------------------
    # موجودی
    # ------------------------------------------------

    if query.data == "balance":

        await query.message.reply_text(
            "💳 موجودی شما:\n\n"
            f"💰 {get_balance(user_id):,}"
        )

        return

    # ------------------------------------------------
    # دارت
    # ------------------------------------------------

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
            "🎯 دارت\n\n"
            "رنگ را انتخاب کن:",
            reply_markup=keyboard
        )

        return

    # ------------------------------------------------
    # رنگ دارت
    # ------------------------------------------------

    if query.data in (
        "dart_white",
        "dart_red"
    ):

        color = (
            "سفید"
            if query.data == "dart_white"
            else "قرمز"
        )

        context.user_data["dart_color"] = color
        context.user_data["state"] = "dart_bet"

        await query.message.reply_text(
            f"🎯 انتخاب: {color}\n\n"
            "💰 تعداد شرط را وارد کن:"
        )

        return

    # ------------------------------------------------
    # تاس
    # ------------------------------------------------

    if query.data == "dice":

        context.user_data.clear()

        context.user_data["state"] = "dice_type"

        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton(
                    "🟢 زوج",
                    callback_data="dice_even"
                ),
                InlineKeyboardButton(
                    "🔵 فرد",
                    callback_data="dice_odd"
                )
            ]
        ])

        await query.message.reply_text(
            "🎲 تاس\n\n"
            "زوج یا فرد را انتخاب کن:",
            reply_markup=keyboard
        )

        return

    # ------------------------------------------------
    # زوج / فرد
    # ------------------------------------------------

    if query.data in (
        "dice_even",
        "dice_odd"
    ):

        choice = (
            "زوج"
            if query.data == "dice_even"
            else "فرد"
        )

        context.user_data["dice_choice"] = choice
        context.user_data["state"] = "dice_bet"

        await query.message.reply_text(
            f"🎲 انتخاب: {choice}\n\n"
            "💰 تعداد شرط را وارد کن:"
        )

        return

    # ------------------------------------------------
    # برداشت
    # ------------------------------------------------

    if query.data == "withdraw":

        context.user_data.clear()

        context.user_data["state"] = "withdraw"

        await query.message.reply_text(
            "💸 برداشت\n\n"
            "تعداد برداشت را وارد کنید:"
        )

        return

    # ------------------------------------------------
    # انتقال مالکیت
    # ------------------------------------------------

    if query.data == "transfer_owner":

        if not is_owner(user_id):

            await query.message.reply_text(
                "❌ این بخش فقط برای مالک است."
            )

            return

        context.user_data.clear()

        context.user_data["state"] = "transfer_owner"

        await query.message.reply_text(
            "👑 انتقال مالکیت\n\n"
            "آیدی عددی طرف را ارسال کن:"
        )

        return

    # ------------------------------------------------
    # شارژ
    # ------------------------------------------------

    if query.data == "charge":

        if not is_owner(user_id):

            await query.message.reply_text(
                "❌ این بخش فقط برای مالک است."
            )

            return

        context.user_data.clear()

        context.user_data["state"] = "charge"

        await query.message.reply_text(
            "💰 شارژ موجودی\n\n"
            "آیدی و تعداد را با فاصله ارسال کن.\n\n"
            "مثال:\n"
            "123456789 50000"
        )

        return


# ==================================================
# دارت
# ==================================================

async def play_dart(update, context, amount):

    user = update.effective_user
    user_id = user.id

    color = context.user_data.get(
        "dart_color"
    )

    if amount < MIN_BET:

        await update.message.reply_text(
            f"❌ حداقل شرط {MIN_BET} است."
        )

        return

    balance = get_balance(user_id)

    if amount > balance:

        await update.message.reply_text(
            "❌ موجودی کافی نیست.\n\n"
            f"💰 موجودی: {balance:,}"
        )

        return

    # کسر شرط
    add_balance(
        user_id,
        -amount
    )

    # دارت در کانال
    msg = await context.bot.send_dice(
        chat_id=CHANNEL_USERNAME,
        emoji="🎯"
    )

    value = msg.dice.value

    # قانون فعلی
    result_color = (
        "سفید"
        if value <= 3
        else "قرمز"
    )

    if result_color == color:

        reward = amount * 2

        add_balance(
            user_id,
            reward
        )

        result = (
            "🎉 برنده شد!\n"
            f"💰 دریافتی: {reward:,}"
        )

    else:

        result = (
            "❌ باخت!\n"
            f"💸 مبلغ: {amount:,}"
        )

    # نتیجه در کانال
    await context.bot.send_message(
        chat_id=CHANNEL_USERNAME,
        text=(
            "🎯 نتیجه دارت\n\n"
            f"👤 {user.first_name}\n"
            f"🆔 {user_id}\n"
            f"🎯 عدد: {value}\n"
            f"🎨 نتیجه: {result_color}\n"
            f"📌 انتخاب: {color}\n"
            f"💰 شرط: {amount:,}\n\n"
            f"{result}"
        )
    )

    await update.message.reply_text(
        "🎯 دارت در کانال انداخته شد.\n\n"
        "📢 کانال 👇\n"
        f"{CHANNEL_LINK}"
    )

    context.user_data.clear()


# ==================================================
# تاس
# ==================================================

async def play_dice(update, context, amount):

    user = update.effective_user
    user_id = user.id

    choice = context.user_data.get(
        "dice_choice"
    )

    if amount < MIN_BET:

        await update.message.reply_text(
            f"❌ حداقل شرط {MIN_BET} است."
        )

        return

    balance = get_balance(user_id)

    if amount > balance:

        await update.message.reply_text(
            "❌ موجودی کافی نیست.\n\n"
            f"💰 موجودی: {balance:,}"
        )

        return

    add_balance(
        user_id,
        -amount
    )

    # تاس در کانال
    msg = await context.bot.send_dice(
        chat_id=CHANNEL_USERNAME,
        emoji="🎲"
    )

    value = msg.dice.value

    result_type = (
        "زوج"
        if value % 2 == 0
        else "فرد"
    )

    if result_type == choice:

        reward = amount * 2

        add_balance(
            user_id,
            reward
        )

        result = (
            "🎉 برنده شد!\n"
            f"💰 دریافتی: {reward:,}"
        )

    else:

        result = (
            "❌ باخت!\n"
            f"💸 مبلغ: {amount:,}"
        )

    # نتیجه در کانال
    await context.bot.send_message(
        chat_id=CHANNEL_USERNAME,
        text=(
            "🎲 نتیجه تاس\n\n"
            f"👤 {user.first_name}\n"
            f"🆔 {user_id}\n"
            f"🎲 عدد: {value}\n"
            f"📌 نتیجه: {result_type}\n"
            f"🎯 انتخاب: {choice}\n"
            f"💰 شرط: {amount:,}\n\n"
            f"{result}"
        )
    )

    await update.message.reply_text(
        "🎲 تاس در کانال انداخته شد.\n\n"
        "📢 کانال 👇\n"
        f"{CHANNEL_LINK}"
    )

    context.user_data.clear()


# ==================================================
# پیام‌های متنی
# ==================================================

async def message_handler(update, context):

    if not await require_membership(
        update,
        context
    ):
        return

    text = update.message.text.strip()

    state = context.user_data.get(
        "state"
    )

    user_id = update.effective_user.id

    # ------------------------------------------------
    # شرط دارت
    # ------------------------------------------------

    if state == "dart_bet":

        try:
            amount = int(text)
        except ValueError:

            await update.message.reply_text(
                "❌ فقط عدد وارد کن."
            )

            return

        await play_dart(
            update,
            context,
            amount
        )

        return

    # ------------------------------------------------
    # شرط تاس
    # ------------------------------------------------

    if state == "dice_bet":

        try:
            amount = int(text)
        except ValueError:

            await update.message.reply_text(
                "❌ فقط عدد وارد کن."
            )

            return

        await play_dice(
            update,
            context,
            amount
        )

        return

    # ------------------------------------------------
    # برداشت
    # ------------------------------------------------

    if state == "withdraw":

        try:
            amount = int(text)
        except ValueError:

            await update.message.reply_text(
                "❌ فقط عدد وارد کن."
            )

            return

        if amount <= 0:

            await update.message.reply_text(
                "❌ تعداد باید بیشتر از صفر باشد."
            )

            return

        balance = get_balance(user_id)

        if amount > balance:

            await update.message.reply_text(
                "❌ موجودی کافی نیست.\n\n"
                f"💰 موجودی: {balance:,}"
            )

            return

        # کسر موجودی
        add_balance(
            user_id,
            -amount
        )

        # ارسال درخواست به کانال
        await context.bot.send_message(
            chat_id=CHANNEL_USERNAME,
            text=(
                "💸 درخواست برداشت\n\n"
                f"👤 نام: {update.effective_user.first_name}\n"
                f"🆔 آیدی عددی: {user_id}\n"
                f"💰 تعداد: {amount:,}\n\n"
                "📌 در انتظار بررسی مالک"
            )
        )

        await update.message.reply_text(
            "✅ درخواست برداشت ثبت شد.\n\n"
            f"💸 تعداد: {amount:,}\n"
            f"💰 موجودی باقی‌مانده: "
            f"{get_balance(user_id):,}\n\n"
            "📢 درخواست در کانال ثبت شد 👇\n"
            f"{CHANNEL_LINK}"
        )

        context.user_data.clear()

        return

    # ------------------------------------------------
    # انتقال مالکیت
    # ------------------------------------------------

    if state == "transfer_owner":

        if not is_owner(user_id):

            context.user_data.clear()

            await update.message.reply_text(
                "❌ فقط مالک اجازه دارد."
            )

            return

        try:
            new_owner_id = int(text)

        except ValueError:

            await update.message.reply_text(
                "❌ آیدی باید عددی باشد."
            )

            return

        if new_owner_id <= 0:

            await update.message.reply_text(
                "❌ آیدی معتبر نیست."
            )

            return

        save_owner(
            new_owner_id
        )

        context.user_data.clear()

        await update.message.reply_text(
            "✅ انتقال مالکیت انجام شد.\n\n"
            f"👑 مالک جدید:\n{new_owner_id}"
        )

        return

    # ------------------------------------------------
    # شارژ
    # ------------------------------------------------

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
                "123456789 50000"
            )

            return

        try:

            target_id = int(parts[0])
            amount = int(parts[1])

        except ValueError:

            await update.message.reply_text(
                "❌ آیدی و مقدار باید عدد باشند."
            )

            return

        if target_id <= 0 or amount <= 0:

            await update.message.reply_text(
                "❌ مقدار نامعتبر است."
            )

            return

        add_balance(
            target_id,
            amount
        )

        context.user_data.clear()

        await update.message.reply_text(
            "✅ شارژ انجام شد.\n\n"
            f"👤 آیدی: {target_id}\n"
            f"💰 شارژ: {amount:,}\n"
            f"💳 موجودی جدید: "
            f"{get_balance(target_id):,}"
        )

        return


# ==================================================
# دستور موجودی
# ==================================================

async def balance_command(update, context):

    if not await require_membership(
        update,
        context
    ):
        return

    user_id = update.effective_user.id

    await update.message.reply_text(
        "💳 موجودی شما:\n\n"
        f"💰 {get_balance(user_id):,}"
    )


# ==================================================
# اجرای ربات
# ==================================================

def main():

    if BOT_TOKEN == "توکن_ربات_اینجا":

        print(
            "❌ BOT_TOKEN را داخل کد وارد کن."
        )

        return

    app = (
        Application
        .builder()
        .token(BOT_TOKEN)
        .build()
    )

    # ----------------------------------------------
    # دستورات
    # ----------------------------------------------

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

    app.add_handler(
        CommandHandler(
            "ownerid",
            ownerid_command
        )
    )

    app.add_handler(
        CommandHandler(
            "reset",
            reset_balance
        )
    )

    app.add_handler(
        CommandHandler(
            "resetbalance",
            reset_balance
        )
    )

    app.add_handler(
        CommandHandler(
            "charge",
            charge_command
        )
    )

    app.add_handler(
        CommandHandler(
            "transferowner",
            transfer_owner_command
        )
    )

    # ----------------------------------------------
    # دکمه‌ها
    # ----------------------------------------------

    app.add_handler(
        CallbackQueryHandler(
            button_handler
        )
    )

    # ----------------------------------------------
    # پیام‌های متنی
    # ----------------------------------------------

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            message_handler
        )
    )

    print("🤖 Bot is running...")

    app.run_polling(
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
