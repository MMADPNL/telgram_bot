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

START_BALANCE = 100000

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
        json.dump(
            data,
            file,
            ensure_ascii=False,
            indent=2
        )


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
    current = get_balance(user_id)
    set_balance(user_id, current + int(amount))


# ==================================================
# ریست همه موجودی‌ها
# ==================================================

def reset_all_balances():
    data = load_balances()

    for uid in data:
        data[uid] = 0

    save_balances(data)

    return len(data)


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

        channel_status = channel_member.status

    except Exception as error:
        print("Channel membership error:", error)
        return False

    try:
        group_member = await bot.get_chat_member(
            GROUP_USERNAME,
            user_id
        )

        group_status = group_member.status

    except Exception as error:
        print("Group membership error:", error)
        return False

    valid_statuses = [
        "member",
        "administrator",
        "creator",
    ]

    return (
        channel_status in valid_statuses
        and
        group_status in valid_statuses
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

    if is_owner(user_id):
        return True

    result = await check_membership(
        context.bot,
        user_id
    )

    if result:
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

def main_keyboard(user_id=None):

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
    ]

    # فقط مالک دکمه ریست را می‌بیند
    if user_id is not None and is_owner(user_id):

        buttons.append([
            InlineKeyboardButton(
                "🔄 ریست موجودی‌ها",
                callback_data="reset_balances"
            )
        ])

    return InlineKeyboardMarkup(buttons)


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

        f"🆔 آیدی عددی شما:\n"
        f"{user.id}\n\n"

        f"💰 موجودی:\n"
        f"{balance:,} امتیاز\n\n"

        "👇 از منوی زیر انتخاب کن:",

        reply_markup=main_keyboard(user.id)
    )


# ==================================================
# دکمه‌ها
# ==================================================

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    # ==================================================
    # بررسی عضویت
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

                "✅ عضویت شما تأیید شد.\n\n"
                "حالا می‌تونی از ربات استفاده کنی.",

                reply_markup=main_keyboard(user_id)
            )

        else:

            await query.message.reply_text(

                "❌ هنوز عضو کانال و گپ نیستی.",

                reply_markup=membership_keyboard()
            )

        return

    # ==================================================
    # عضویت اجباری
    # ==================================================

    if not await require_membership(update, context):
        return

    # ==================================================
    # ریست موجودی‌ها
    # ==================================================

    if query.data == "reset_balances":

        if not is_owner(user_id):

            await query.message.reply_text(
                "❌ فقط مالک اجازه ریست موجودی‌ها را دارد."
            )

            return

        count = reset_all_balances()

        await query.message.reply_text(

            "✅ ریست موجودی‌ها انجام شد.\n\n"

            f"👥 تعداد کاربران ریست‌شده: {count}\n"
            "💰 موجودی همه کاربران: 0 امتیاز"
        )

        return

    # ==================================================
    # موجودی
    # ==================================================

    if query.data == "balance":

        balance = get_balance(user_id)

        await query.message.reply_text(

            "💳 موجودی شما:\n\n"
            f"💰 {balance:,} امتیاز"
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

    # ==================================================
    # رنگ دارت
    # ==================================================

    if query.data in [
        "dart_white",
        "dart_red"
    ]:

        if query.data == "dart_white":
            color = "سفید"
        else:
            color = "قرمز"

        context.user_data["dart_color"] = color
        context.user_data["state"] = "dart_bet"

        await query.message.reply_text(

            f"🎯 انتخاب شما: {color}\n\n"
            "💰 تعداد شرط را وارد کنید:\n\n"
            f"حداقل شرط: {MIN_BET:,}"
        )

        return

    # ==================================================
    # تاس
    # ==================================================

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

            "🎲 بازی تاس\n\n"
            "انتخاب کن:",

            reply_markup=keyboard
        )

        return

    # ==================================================
    # زوج / فرد
    # ==================================================

    if query.data in [
        "dice_even",
        "dice_odd"
    ]:

        if query.data == "dice_even":
            choice = "زوج"
        else:
            choice = "فرد"

        context.user_data["dice_choice"] = choice
        context.user_data["state"] = "dice_bet"

        await query.message.reply_text(

            f"🎲 انتخاب شما: {choice}\n\n"
            "💰 تعداد شرط را وارد کنید:\n\n"
            f"حداقل شرط: {MIN_BET:,}"
        )

        return

    # ==================================================
    # برداشت
    # ==================================================

    if query.data == "withdraw":

        context.user_data.clear()

        context.user_data["state"] = "withdraw"

        await query.message.reply_text(

            "💸 برداشت\n\n"
            "تعداد برداشت را وارد کنید:"
        )

        return

    # ==================================================
    # انتقال مالکیت
    # ==================================================

    if query.data == "transfer_owner":

        if not is_owner(user_id):

            await query.message.reply_text(
                "❌ این بخش فقط برای مالک فعال است."
            )

            return

        context.user_data.clear()

        context.user_data["state"] = "transfer_owner"

        await query.message.reply_text(

            "👑 انتقال مالکیت\n\n"
            "آیدی عددی طرف را ارسال کن:"
        )

        return

    # ==================================================
    # شارژ موجودی
    # ==================================================

    if query.data == "charge":

        if not is_owner(user_id):

            await query.message.reply_text(
                "❌ این بخش فقط برای مالک فعال است."
            )

            return

        context.user_data.clear()

        context.user_data["state"] = "charge"

        await query.message.reply_text(

            "💰 شارژ موجودی\n\n"
            "آیدی عددی و تعداد را با فاصله ارسال کن.\n\n"

            "مثال:\n"
            "123456789 50000"
        )

        return


# ==================================================
# بازی دارت
# ==================================================

async def play_dart(update, context, amount):

    user = update.effective_user

    user_id = user.id

    selected_color = context.user_data.get(
        "dart_color"
    )

    if amount < MIN_BET:

        await update.message.reply_text(

            f"❌ حداقل شرط {MIN_BET:,} امتیاز است."
        )

        return

    balance = get_balance(user_id)

    if amount > balance:

        await update.message.reply_text(

            "❌ موجودی کافی نیست.\n\n"
            f"💰 موجودی شما: {balance:,}"
        )

        return

    add_balance(
        user_id,
        -amount
    )

    dice_message = await context.bot.send_dice(

        chat_id=CHANNEL_USERNAME,

        emoji="🎯"
    )

    value = dice_message.dice.value

    if value <= 3:
        result_color = "سفید"
    else:
        result_color = "قرمز"

    if result_color == selected_color:

        reward = amount * 2

        add_balance(
            user_id,
            reward
        )

        result_text = (
            "🎉 برنده شد!\n"
            f"💰 دریافتی: {reward:,} امتیاز"
        )

    else:

        result_text = (
            "❌ باخت!\n"
            f"💸 باخت: {amount:,} امتیاز"
        )

    await context.bot.send_message(

        chat_id=CHANNEL_USERNAME,

        text=(

            "🎯 نتیجه دارت\n\n"

            f"👤 نام: {user.first_name}\n"
            f"🆔 آیدی: {user_id}\n\n"

            f"🎯 عدد دارت: {value}\n"
            f"🎨 نتیجه: {result_color}\n"
            f"📌 انتخاب کاربر: {selected_color}\n"
            f"💰 شرط: {amount:,}\n\n"

            f"{result_text}"
        )
    )

    await update.message.reply_text(

        "🎯 دارت در کانال انداخته شد.\n\n"

        "📢 در کانال 👇\n"
        f"{CHANNEL_LINK}"
    )

    context.user_data.clear()


# ==================================================
# بازی تاس
# ==================================================

async def play_dice(update, context, amount):

    user = update.effective_user

    user_id = user.id

    selected = context.user_data.get(
        "dice_choice"
    )

    if amount < MIN_BET:

        await update.message.reply_text(

            f"❌ حداقل شرط {MIN_BET:,} امتیاز است."
        )

        return

    balance = get_balance(user_id)

    if amount > balance:

        await update.message.reply_text(

            "❌ موجودی کافی نیست.\n\n"
            f"💰 موجودی شما: {balance:,}"
        )

        return

    add_balance(
        user_id,
        -amount
    )

    dice_message = await context.bot.send_dice(

        chat_id=CHANNEL_USERNAME,

        emoji="🎲"
    )

    value = dice_message.dice.value

    if value % 2 == 0:
        result_type = "زوج"
    else:
        result_type = "فرد"

    if result_type == selected:

        reward = amount * 2

        add_balance(
            user_id,
            reward
        )

        result_text = (
            "🎉 برنده شد!\n"
            f"💰 دریافتی: {reward:,} امتیاز"
        )

    else:

        result_text = (
            "❌ باخت!\n"
            f"💸 باخت: {amount:,} امتیاز"
        )

    await context.bot.send_message(

        chat_id=CHANNEL_USERNAME,

        text=(

            "🎲 نتیجه تاس\n\n"

            f"👤 نام: {user.first_name}\n"
            f"🆔 آیدی: {user_id}\n\n"

            f"🎲 عدد تاس: {value}\n"
            f"📌 نتیجه: {result_type}\n"
            f"🎯 انتخاب کاربر: {selected}\n"
            f"💰 شرط: {amount:,}\n\n"

            f"{result_text}"
        )
    )

    await update.message.reply_text(

        "🎲 تاس در کانال انداخته شد.\n\n"

        "📢 در کانال 👇\n"
        f"{CHANNEL_LINK}"
    )

    context.user_data.clear()


# ==================================================
# پیام‌های متنی
# ==================================================

async def message_handler(update, context):

    if not await require_membership(update, context):
        return

    text = update.message.text.strip()

    state = context.user_data.get(
        "state"
    )

    user_id = update.effective_user.id

    # ==================================================
    # مبلغ دارت
    # ==================================================

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

    # ==================================================
    # مبلغ تاس
    # ==================================================

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

    # ==================================================
    # برداشت
    # ==================================================

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
                f"💰 موجودی شما: {balance:,}"
            )

            return

        add_balance(
            user_id,
            -amount
        )

        await context.bot.send_message(

            chat_id=CHANNEL_USERNAME,

            text=(

                "💸 درخواست برداشت\n\n"

                f"👤 نام: {update.effective_user.first_name}\n"
                f"🆔 آیدی عددی: {user_id}\n"
                f"💰 تعداد برداشت: {amount:,}\n\n"

                "📌 وضعیت: در انتظار بررسی مالک"
            )
        )

        new_balance = get_balance(
            user_id
        )

        await update.message.reply_text(

            "✅ درخواست برداشت ثبت شد.\n\n"

            f"💸 تعداد: {amount:,}\n"
            f"💰 موجودی باقی‌مانده: {new_balance:,}\n\n"

            "📢 درخواست در کانال ارسال شد 👇\n"
            f"{CHANNEL_LINK}"
        )

        context.user_data.clear()

        return

    # ==================================================
    # انتقال مالکیت
    # ==================================================

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

            f"👑 مالک جدید:\n"
            f"{new_owner_id}"
        )

        return

    # ==================================================
    # شارژ موجودی
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
                "123456789 50000"
            )

            return

        try:

            target_id = int(parts[0])
            amount = int(parts[1])

        except ValueError:

            await update.message.reply_text(
                "❌ آیدی و تعداد باید عدد باشند."
            )

            return

        if target_id <= 0:

            await update.message.reply_text(
                "❌ آیدی معتبر نیست."
            )

            return

        if amount <= 0:

            await update.message.reply_text(
                "❌ تعداد باید بیشتر از صفر باشد."
            )

            return

        add_balance(
            target_id,
            amount
        )

        new_balance = get_balance(
            target_id
        )

        context.user_data.clear()

        await update.message.reply_text(

            "✅ موجودی شارژ شد.\n\n"

            f"👤 آیدی: {target_id}\n"
            f"💰 شارژ: {amount:,}\n"
            f"💳 موجودی جدید: {new_balance:,}"
        )

        return


# ==================================================
# دستور موجودی
# ==================================================

async def balance_command(update, context):

    if not await require_membership(update, context):
        return

    user_id = update.effective_user.id

    await update.message.reply_text(

        "💳 موجودی شما:\n\n"
        f"💰 {get_balance(user_id):,} امتیاز"
    )


# ==================================================
# اجرای ربات
# ==================================================

def main():

    if BOT_TOKEN == "توکن_ربات_را_اینجا_بگذار":

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
        CallbackQueryHandler(
            button_handler
        )
    )

    app.add_handler(
        MessageHandler(
            filters.TEXT & ~filters.COMMAND,
            message_handler
        )
    )

    print(
        "🤖 Bot is running..."
    )

    app.run_polling(
        drop_pending_updates=True
    )


if __name__ == "__main__":
    main()
