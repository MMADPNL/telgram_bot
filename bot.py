import json
import os
import asyncio

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

from config import BOT_TOKEN


OWNER_ID = 8552447077

CHANNEL_USERNAME = "@MMAD_KING1W"
GROUP_USERNAME = "@gap_bazi12"

CHANNEL_LINK = "https://t.me/MMAD_KING1W"
GROUP_LINK = "https://t.me/gap_bazi12"

BALANCE_FILE = "balances.json"
OWNER_FILE = "owner.json"

START_BALANCE = 0
MIN_BET = 100

# جلوگیری از اجرای همزمان چند بازی برای یک کاربر
ACTIVE_GAMES = set()

# جلوگیری از درخواست‌های همزمان موجودی
BALANCE_LOCK = asyncio.Lock()


# ==================================================
# BALANCE
# ==================================================

def load_balances():
    if not os.path.exists(BALANCE_FILE):
        return {}

    try:
        with open(BALANCE_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)

        if isinstance(data, dict):
            return data

    except Exception as e:
        print("BALANCE LOAD ERROR:", e)

    return {}


def save_balances(data):
    temp_file = BALANCE_FILE + ".tmp"

    with open(temp_file, "w", encoding="utf-8") as f:
        json.dump(
            data,
            f,
            ensure_ascii=False,
            indent=2
        )

    os.replace(temp_file, BALANCE_FILE)


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

    amount = int(amount)

    if amount < 0:
        amount = 0

    data[str(user_id)] = amount

    save_balances(data)


def add_balance(user_id, amount):
    current = get_balance(user_id)

    new_balance = current + int(amount)

    if new_balance < 0:
        new_balance = 0

    set_balance(
        user_id,
        new_balance
    )

    return new_balance


# ==================================================
# OWNER
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
    elif update.message:
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
        f"💰 موجودی:\n{balance:,} 🪙\n\n"
        "👇 از منوی زیر انتخاب کن:",
        reply_markup=main_keyboard(user.id)
    )


# ==================================================
# RESET
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

        await update.message.reply_text(
            "✅ ریست موجودی انجام شد.\n\n"
            "💰 موجودی تمام کاربران صفر شد."
        )

    except Exception as e:

        print("RESET ERROR:", e)

        await update.message.reply_text(
            f"❌ خطا در ریست:\n{e}"
        )


# ==================================================
# DART
# ==================================================

async def play_dart(update, context, amount):

    user = update.effective_user
    user_id = user.id

    selected_color = context.user_data.get(
        "dart_color"
    )

    if selected_color not in ("سفید", "قرمز"):
        context.user_data.clear()

        await update.message.reply_text(
            "❌ انتخاب دارت نامعتبر است."
        )

        return

    if amount < MIN_BET:

        await update.message.reply_text(
            f"❌ حداقل شرط {MIN_BET:,} است."
        )

        return

    balance = get_balance(user_id)

    if amount > balance:

        await update.message.reply_text(
            "❌ موجودی کافی نیست.\n\n"
            f"💰 موجودی: {balance:,}"
        )

        return

    if user_id in ACTIVE_GAMES:

        await update.message.reply_text(
            "⏳ یک بازی برای شما در حال انجام است."
        )

        return

    ACTIVE_GAMES.add(user_id)

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
            "💰 مبلغ شرط به شما برگشت داده شد."
        )

        ACTIVE_GAMES.discard(user_id)
        context.user_data.clear()

        return

    # Telegram Dart:
    # 1 تا 3 = سفید
    # 4 تا 6 = قرمز
    result_color = (
        "سفید"
        if value <= 3
        else "قرمز"
    )

    won = result_color == selected_color

    if won:

        reward = amount * 2

        new_balance = add_balance(
            user_id,
            reward
        )

        result_text = (
            "🎉 برنده شد!\n"
            f"💰 جایزه: {reward:,}\n"
            f"💳 موجودی جدید: {new_balance:,}"
        )

    else:

        new_balance = get_balance(user_id)

        result_text = (
            "❌ باخت!\n"
            f"💸 مبلغ باخته‌شده: {amount:,}\n"
            f"💳 موجودی جدید: {new_balance:,}"
        )

    # ارسال نتیجه به کانال
    try:

        await context.bot.send_message(
            chat_id=CHANNEL_USERNAME,
            text=(
                "🎯 نتیجه دارت\n\n"
                f"👤 نام: {user.first_name}\n"
                f"🆔 آیدی: {user_id}\n"
                f"🎯 عدد دارت: {value}\n"
                f"🎨 رنگ واقعی: {result_color}\n"
                f"📌 انتخاب کاربر: {selected_color}\n"
                f"💰 شرط: {amount:,}\n\n"
                f"{result_text}"
            )
        )

    except Exception as e:

        print("DART CHANNEL ERROR:", e)

    await update.message.reply_text(
        "🎯 نتیجه دارت\n\n"
        f"🎯 عدد: {value}\n"
        f"🎨 رنگ: {result_color}\n"
        f"📌 انتخاب شما: {selected_color}\n\n"
        f"{result_text}"
    )

    ACTIVE_GAMES.discard(user_id)
    context.user_data.clear()


# ==================================================
# DICE
# ==================================================

async def play_dice(update, context, amount):

    user = update.effective_user
    user_id = user.id

    selected = context.user_data.get(
        "dice_choice"
    )

    if selected not in ("زوج", "فرد"):

        context.user_data.clear()

        await update.message.reply_text(
            "❌ انتخاب تاس نامعتبر است."
        )

        return

    if amount < MIN_BET:

        await update.message.reply_text(
            f"❌ حداقل شرط {MIN_BET:,} است."
        )

        return

    balance = get_balance(user_id)

    if amount > balance:

        await update.message.reply_text(
            "❌ موجودی کافی نیست.\n\n"
            f"💰 موجودی: {balance:,}"
        )

        return

    if user_id in ACTIVE_GAMES:

        await update.message.reply_text(
            "⏳ یک بازی برای شما در حال انجام است."
        )

        return

    ACTIVE_GAMES.add(user_id)

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
            "💰 مبلغ شرط به شما برگشت داده شد."
        )

        ACTIVE_GAMES.discard(user_id)
        context.user_data.clear()

        return

    result_type = (
        "زوج"
        if value % 2 == 0
        else "فرد"
    )

    won = result_type == selected

    if won:

        reward = amount * 2

        new_balance = add_balance(
            user_id,
            reward
        )

        result_text = (
            "🎉 برنده شد!\n"
            f"💰 جایزه: {reward:,}\n"
            f"💳 موجودی جدید: {new_balance:,}"
        )

    else:

        new_balance = get_balance(user_id)

        result_text = (
            "❌ باخت!\n"
            f"💸 مبلغ باخته‌شده: {amount:,}\n"
            f"💳 موجودی جدید: {new_balance:,}"
        )

    try:

        await context.bot.send_message(
            chat_id=CHANNEL_USERNAME,
            text=(
                "🎲 نتیجه تاس\n\n"
                f"👤 نام: {user.first_name}\n"
                f"🆔 آیدی: {user_id}\n"
                f"🎲 عدد تاس: {value}\n"
                f"📌 نتیجه واقعی: {result_type}\n"
                f"🎯 انتخاب کاربر: {selected}\n"
                f"💰 شرط: {amount:,}\n\n"
                f"{result_text}"
            )
        )

    except Exception as e:

        print("DICE CHANNEL ERROR:", e)

    await update.message.reply_text(
        "🎲 نتیجه تاس\n\n"
        f"🎲 عدد: {value}\n"
        f"📌 نتیجه: {result_type}\n"
        f"🎯 انتخاب شما: {selected}\n\n"
        f"{result_text}"
    )

    ACTIVE_GAMES.discard(user_id)
    context.user_data.clear()


# ==================================================
# BUTTON HANDLER
# ==================================================

async def button_handler(update, context):

    query = update.callback_query

    await query.answer()

    user_id = query.from_user.id

    # --------------------------------------------------
    # CHECK MEMBERSHIP
    # --------------------------------------------------

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

    # --------------------------------------------------
    # MEMBERSHIP
    # --------------------------------------------------

    if not await require_membership(
        update,
        context
    ):
        return

    # --------------------------------------------------
    # BALANCE
    # --------------------------------------------------

    if query.data == "balance":

        await query.message.reply_text(
            "💳 موجودی شما:\n\n"
            f"💰 {get_balance(user_id):,} 🪙"
        )

        return

    # --------------------------------------------------
    # RESET
    # --------------------------------------------------

    if query.data == "reset_balance":

        if not is_owner(user_id):

            await query.message.reply_text(
                "❌ فقط مالک اجازه دارد."
            )

            return

        try:

            save_balances({})

            await query.message.reply_text(
                "✅ ریست موجودی انجام شد.\n\n"
                "💰 موجودی تمام کاربران صفر شد."
            )

        except Exception as e:

            print("RESET BUTTON ERROR:", e)

            await query.message.reply_text(
                f"❌ خطا:\n{e}"
            )

        return

    # --------------------------------------------------
    # DART
    # --------------------------------------------------

    if query.data == "dart":

        if user_id in ACTIVE_GAMES:

            await query.message.reply_text(
                "⏳ یک بازی برای شما در حال انجام است."
            )

            return

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

    # --------------------------------------------------
    # DART COLOR
    # --------------------------------------------------

    if query.data in (
        "dart_white",
        "dart_red"
    ):

        if user_id in ACTIVE_GAMES:

            await query.message.reply_text(
                "⏳ یک بازی برای شما در حال انجام است."
            )

            return

        color = (
            "سفید"
            if query.data == "dart_white"
            else "قرمز"
        )

        context.user_data["dart_color"] = color
        context.user_data["state"] = "dart_bet"

        await query.message.reply_text(
            f"🎯 انتخاب شما: {color}\n\n"
            "💰 مبلغ شرط را وارد کن:\n"
            f"حداقل: {MIN_BET:,}"
        )

        return

    # --------------------------------------------------
    # DICE
    # --------------------------------------------------

    if query.data == "dice":

        if user_id in ACTIVE_GAMES:

            await query.message.reply_text(
                "⏳ یک بازی برای شما در حال انجام است."
            )

            return

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

    # --------------------------------------------------
    # DICE TYPE
    # --------------------------------------------------

    if query.data in (
        "dice_even",
        "dice_odd"
    ):

        if user_id in ACTIVE_GAMES:

            await query.message.reply_text(
                "⏳ یک بازی برای شما در حال انجام است."
            )

            return

        choice = (
            "زوج"
            if query.data == "dice_even"
            else "فرد"
        )

        context.user_data["dice_choice"] = choice
        context.user_data["state"] = "dice_bet"

        await query.message.reply_text(
            f"🎲 انتخاب شما: {choice}\n\n"
            "💰 مبلغ شرط را وارد کن:\n"
            f"حداقل: {MIN_BET:,}"
        )

        return

    # --------------------------------------------------
    # WITHDRAW
    # --------------------------------------------------

    if query.data == "withdraw":

        if user_id in ACTIVE_GAMES:

            await query.message.reply_text(
                "⏳ ابتدا بازی فعلی را تمام کن."
            )

            return

        context.user_data.clear()

        context.user_data["state"] = "withdraw"

        await query.message.reply_text(
            "💸 برداشت\n\n"
            "تعداد برداشت را وارد کنید:"
        )

        return

    # --------------------------------------------------
    # TRANSFER OWNER
    # --------------------------------------------------

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

    # --------------------------------------------------
    # CHARGE
    # --------------------------------------------------

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
# MESSAGE HANDLER
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

    state = context.user_data.get("state")

    user_id = update.effective_user.id

    # --------------------------------------------------
    # DART BET
    # --------------------------------------------------

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

    # --------------------------------------------------
    # DICE BET
    # --------------------------------------------------

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

    # --------------------------------------------------
    # WITHDRAW
    # --------------------------------------------------

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

        # ابتدا کسر می‌کنیم
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
                    f"🆔 آیدی کاربر: {user_id}\n"
                    f"💰 تعداد برداشت: {amount:,}\n\n"
                    "📌 وضعیت: در انتظار بررسی مالک"
                )
            )

        except Exception as e:

            # اگر ارسال به کانال شکست خورد، پول برگردد
            add_balance(
                user_id,
                amount
            )

            print("WITHDRAW ERROR:", e)

            await update.message.reply_text(
                "❌ ارسال درخواست برداشت انجام نشد.\n\n"
                "💰 مبلغ به موجودی شما برگشت داده شد."
            )

            return

        new_balance = get_balance(user_id)

        await update.message.reply_text(
            "✅ درخواست برداشت ثبت شد.\n\n"
            f"💸 مبلغ برداشت: {amount:,}\n"
            f"💰 موجودی باقی‌مانده: {new_balance:,}\n\n"
            f"📢 {CHANNEL_LINK}"
        )

        context.user_data.clear()

        return

    # --------------------------------------------------
    # TRANSFER OWNER
    # --------------------------------------------------

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

        save_owner(new_owner_id)

        context.user_data.clear()

        await update.message.reply_text(
            "✅ انتقال مالکیت انجام شد.\n\n"
            f"👑 مالک جدید:\n{new_owner_id}"
        )

        return

    # --------------------------------------------------
    # CHARGE
    # --------------------------------------------------

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

        new_balance = add_balance(
            target_id,
            amount
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
        f"💰 {get_balance(user_id):,} 🪙"
    )


# ==================================================
# ERROR HANDLER
# ==================================================

async def error_handler(update, context):

    print(
        "BOT ERROR:",
        repr(context.error)
    )


# ==================================================
# MAIN
# ==================================================

def main():

    if not BOT_TOKEN:

        print(
            "❌ BOT_TOKEN در GitHub Secrets پیدا نشد."
        )

        return

    print("🤖 Bot is starting...")

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

    app.add_error_handler(
        error_handler
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
