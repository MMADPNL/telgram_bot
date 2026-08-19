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
# BALANCE FUNCTIONS
# ==================================================

def load_balances():
    if not os.path.exists(BALANCE_FILE):
        return {}

    try:
        with open(BALANCE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict):
            return data

        return {}

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

    except (ValueError, TypeError):
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
# OWNER FUNCTIONS
# ==================================================

def save_owner(user_id):
    with open(OWNER_FILE, "w", encoding="utf-8") as f:
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
        with open(OWNER_FILE, "r", encoding="utf-8") as f:
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

        valid_statuses = {
            "member",
            "administrator",
            "creator"
        }

        return (
            channel_member.status in valid_statuses
            and
            group_member.status in valid_statuses
        )

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
                "💸 برداشت",
                callback_data="withdraw"
            )
        ],
        [
            InlineKeyboardButton(
                "💳 موجودی",
                callback_data="balance"
            )
        ]
    ]

    # فقط مالک این دکمه‌ها را می‌بیند
    if is_owner(user_id):

        buttons.append([
            InlineKeyboardButton(
                "💰 شارژ موجودی",
                callback_data="charge"
            )
        ])

        buttons.append([
            InlineKeyboardButton(
                "👑 انتقال مالکیت",
                callback_data="transfer_owner"
            )
        ])

        buttons.append([
            InlineKeyboardButton(
                "🔄 ریست موجودی",
                callback_data="reset_balance"
            )
        ])

    return InlineKeyboardMarkup(buttons)


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
        "👇 از منوی زیر انتخاب کن:",
        reply_markup=main_keyboard(user.id)
    )


# ==================================================
# RESET BALANCE
# ==================================================

async def reset_balance(update, context):

    user_id = update.effective_user.id

    if not is_owner(user_id):
        await update.message.reply_text(
            "❌ فقط مالک می‌تواند موجودی‌ها را ریست کند."
        )
        return

    try:
        save_balances({})

        if load_balances() != {}:
            await update.message.reply_text(
                "❌ ریست انجام نشد."
            )
            return

        await update.message.reply_text(
            "✅ ریست موجودی انجام شد!\n\n"
            "💰 موجودی تمام کاربران: 0\n"
            "🗑 موجودی‌های قبلی پاک شدند."
        )

    except Exception as e:
        print("RESET ERROR:", e)

        await update.message.reply_text(
            f"❌ خطا در ریست:\n{e}"
        )


# ==================================================
# BUTTON HANDLER
# ==================================================

async def button_handler(update, context):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    # ==================================================
    # CHECK MEMBERSHIP
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

        await query.message.reply_text(
            "💳 موجودی شما:\n\n"
            f"💰 {get_balance(user_id):,}"
        )

        return

    # ==================================================
    # RESET BALANCE
    # ==================================================

    if query.data == "reset_balance":

        if not is_owner(user_id):
            await query.message.reply_text(
                "❌ این بخش فقط برای مالک فعال است."
            )
            return

        try:
            save_balances({})

            await query.message.reply_text(
                "✅ ریست موجودی انجام شد!\n\n"
                "💰 موجودی تمام کاربران صفر شد."
            )

        except Exception as e:
            print("RESET BUTTON ERROR:", e)

            await query.message.reply_text(
                f"❌ خطا:\n{e}"
            )

        return

    # ==================================================
    # DART
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
            "🎯 دارت\n\n"
            "اول رنگ را انتخاب کن:",
            reply_markup=keyboard
        )

        return

    # ==================================================
    # DART COLOR
    # ==================================================

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
            f"🎯 انتخاب شما: {color}\n\n"
            "💰 تعداد شرط را وارد کنید:\n"
            f"حداقل: {MIN_BET}"
        )

        return

    # ==================================================
    # DICE
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
            "🎲 تاس\n\n"
            "زوج یا فرد را انتخاب کن:",
            reply_markup=keyboard
        )

        return

    # ==================================================
    # DICE TYPE
    # ==================================================

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
            f"🎲 انتخاب شما: {choice}\n\n"
            "💰 تعداد شرط را وارد کنید:\n"
            f"حداقل: {MIN_BET}"
        )

        return

    # ==================================================
    # WITHDRAW
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
            "آیدی عددی مالک جدید را ارسال کن:"
        )

        return

    # ==================================================
    # CHARGE
    # ==================================================

    if query.data == "charge":

        if not is_owner(user_id):
            await query.message.reply_text(
                "❌ فقط مالک اجازه دارد."
            )
            return

        context.user_data.clear()

        context.user_data["state"] = "charge"

        await query.message.reply_text(
            "💰 شارژ موجودی\n\n"
            "آیدی عددی و مقدار را با فاصله ارسال کن.\n\n"
            "مثال:\n"
            "123456789 50000"
        )

        return


# ==================================================
# DART GAME
# ==================================================

async def play_dart(update, context, amount):

    user = update.effective_user
    user_id = user.id

    selected_color = context.user_data.get(
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

    add_balance(
        user_id,
        -amount
    )

    try:

        dice_message = await context.bot.send_dice(
            chat_id=CHANNEL_USERNAME,
            emoji="🎯"
        )

        value = dice_message.dice.value

    except Exception as e:

        add_balance(
            user_id,
            amount
        )

        print("DART ERROR:", e)

        await update.message.reply_text(
            "❌ ارسال دارت انجام نشد.\n\n"
            "💰 شرط شما برگشت داده شد."
        )

        return

    result_color = (
        "سفید"
        if value <= 3
        else "قرمز"
    )

    if result_color == selected_color:

        reward = amount * 2

        add_balance(
            user_id,
            reward
        )

        result_text = (
            "🎉 برنده شد!\n"
            f"💰 دریافتی: {reward:,}"
        )

    else:

        result_text = (
            "❌ باخت!\n"
            f"💸 باخت: {amount:,}"
        )

    try:

        await context.bot.send_message(
            chat_id=CHANNEL_USERNAME,
            text=(
                "🎯 نتیجه دارت\n\n"
                f"👤 نام: {user.first_name}\n"
                f"🆔 آیدی: {user_id}\n"
                f"🎯 عدد: {value}\n"
                f"🎨 نتیجه: {result_color}\n"
                f"📌 انتخاب: {selected_color}\n"
                f"💰 شرط: {amount:,}\n\n"
                f"{result_text}"
            )
        )

    except Exception as e:
        print("DART RESULT ERROR:", e)

    await update.message.reply_text(
        "🎯 دارت در کانال انداخته شد.\n\n"
        f"📢 {CHANNEL_LINK}"
    )

    context.user_data.clear()


# ==================================================
# DICE GAME
# ==================================================

async def play_dice(update, context, amount):

    user = update.effective_user
    user_id = user.id

    selected = context.user_data.get(
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

    try:

        dice_message = await context.bot.send_dice(
            chat_id=CHANNEL_USERNAME,
            emoji="🎲"
        )

        value = dice_message.dice.value

    except Exception as e:

        add_balance(
            user_id,
            amount
        )

        print("DICE ERROR:", e)

        await update.message.reply_text(
            "❌ ارسال تاس انجام نشد.\n\n"
            "💰 شرط شما برگشت داده شد."
        )

        return

    result_type = (
        "زوج"
        if value % 2 == 0
        else "فرد"
    )

    if result_type == selected:

        reward = amount * 2

        add_balance(
            user_id,
            reward
        )

        result_text = (
            "🎉 برنده شد!\n"
            f"💰 دریافتی: {reward:,}"
        )

    else:

        result_text = (
            "❌ باخت!\n"
            f"💸 باخت: {amount:,}"
        )

    try:

        await context.bot.send_message(
            chat_id=CHANNEL_USERNAME,
            text=(
                "🎲 نتیجه تاس\n\n"
                f"👤 نام: {user.first_name}\n"
                f"🆔 آیدی: {user_id}\n"
                f"🎲 عدد: {value}\n"
                f"📌 نتیجه: {result_type}\n"
                f"🎯 انتخاب: {selected}\n"
                f"💰 شرط: {amount:,}\n\n"
                f"{result_text}"
            )
        )

    except Exception as e:
        print("DICE RESULT ERROR:", e)

    await update.message.reply_text(
        "🎲 تاس در کانال انداخته شد.\n\n"
        f"📢 {CHANNEL_LINK}"
    )

    context.user_data.clear()


# ==================================================
# TEXT HANDLER
# ==================================================

async def message_handler(update, context):

    if not await require_membership(
        update,
        context
    ):
        return

    if not update.message:
        return

    if not update.message.text:
        return

    text = update.message.text.strip()

    state = context.user_data.get(
        "state"
    )

    user_id = update.effective_user.id

    # ==================================================
    # DART BET
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
    # DICE BET
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
    # WITHDRAW
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
                "❌ مقدار باید بیشتر از صفر باشد."
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

        try:

            await context.bot.send_message(
                chat_id=CHANNEL_USERNAME,
                text=(
                    "💸 درخواست برداشت\n\n"
                    f"👤 نام: {update.effective_user.first_name}\n"
                    f"🆔 آیدی: {user_id}\n"
                    f"💰 مبلغ: {amount:,}\n\n"
                    "📌 وضعیت: در انتظار بررسی مالک"
                )
            )

        except Exception as e:

            add_balance(
                user_id,
                amount
            )

            print(
                "WITHDRAW ERROR:",
                e
            )

            await update.message.reply_text(
                "❌ ارسال درخواست انجام نشد.\n\n"
                "💰 موجودی شما برگشت داده شد."
            )

            return

        new_balance = get_balance(user_id)

        await update.message.reply_text(
            "✅ درخواست برداشت ثبت شد.\n\n"
            f"💸 مبلغ: {amount:,}\n"
            f"💰 موجودی باقی‌مانده: {new_balance:,}\n\n"
            f"📢 {CHANNEL_LINK}"
        )

        context.user_data.clear()

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

        if target_id <= 0:

            await update.message.reply_text(
                "❌ آیدی معتبر نیست."
            )

            return

        if amount <= 0:

            await update.message.reply_text(
                "❌ مقدار باید بیشتر از صفر باشد."
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
# BALANCE COMMAND
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
# MAIN
# ==================================================

def main():

    if BOT_TOKEN == "توکن_ربات_اینجا":

        print("❌ BOT_TOKEN را وارد کن.")

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

    print("🤖 Bot is running...")

    app.run_polling(
        drop_pending_updates=True
    )


# ==================================================
# RUN
# ==================================================

if __name__ == "__main__":
    main()
