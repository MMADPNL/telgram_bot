import json
import os
import random
import re
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# ========== توکن و تنظیمات ==========
TOKEN = "8981045477:AAHCiu01fynQ0mkwCTS_W4wlnIZfawdlzLM"  # توکن خودت
OWNER_ID = 123456789  # <-- آیدی عددی خودت رو از @userinfobot بگیر و اینجا بذار

DATA_FILE = "balances.json"
STATS_FILE = "stats.json"

# ========== توابع دیتا (موجودی) ==========
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    with open(DATA_FILE, "r") as f:
        return json.load(f)

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_balance(user_id):
    data = load_data()
    return data.get(str(user_id), 0)

def set_balance(user_id, amount):
    data = load_data()
    data[str(user_id)] = amount
    save_data(data)

def add_balance(user_id, amount):
    current = get_balance(user_id)
    set_balance(user_id, current + amount)

# ========== توابع دیتا (آمار) ==========
def load_stats():
    if not os.path.exists(STATS_FILE):
        return {}
    with open(STATS_FILE, "r") as f:
        return json.load(f)

def save_stats(data):
    with open(STATS_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_stats(user_id):
    data = load_stats()
    return data.get(str(user_id), {"wins": 0, "losses": 0, "draws": 0})

def update_stats(user_id, result):
    data = load_stats()
    user_id = str(user_id)
    if user_id not in data:
        data[user_id] = {"wins": 0, "losses": 0, "draws": 0}
    data[user_id][result] += 1
    save_stats(data)

# ========== صفحه کلید شیشه‌ای ==========
def get_game_keyboard():
    keyboard = [
        [InlineKeyboardButton("🎲 تاس", callback_data="game_dice")],
        [InlineKeyboardButton("🏀 بسکتبال", callback_data="game_basketball")],
        [InlineKeyboardButton("🎳 بولینگ", callback_data="game_bowling")],
        [InlineKeyboardButton("🎯 دارت", callback_data="game_dart")],
        [InlineKeyboardButton("💰 موجودی", callback_data="balance")],
        [InlineKeyboardButton("📊 آمار", callback_data="stats")],
    ]
    return InlineKeyboardMarkup(keyboard)

# ========== شروع ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        "🎮 **به ربات بازی خوش اومدی!**\n\n"
        "📌 **فرمت بازی:**\n"
        "`1تاس 200`\n"
        "`1بسکتبال 150`\n"
        "`1بولینگ 100`\n"
        "`1دارت 300`\n\n"
        "💰 شرط: **۵۰** تا **۵۰۰۰** سکه\n"
        "📊 آمار برد/باخت/مساوی ذخیره میشه\n\n"
        "❗ یا از دکمه‌های زیر استفاده کن:",
        reply_markup=get_game_keyboard()
    )

# ========== پردازش دستورات با فرمت 1بازی ==========
async def handle_game_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = update.message.text.strip()
    user_id = update.effective_user.id

    pattern = r'^1(تاس|بسکتبال|بولینگ|دارت)\s+(\d+)$'
    match = re.match(pattern, text)

    if not match:
        await update.message.reply_text(
            "❌ **فرمت دستور اشتباه است!**\n\n"
            "📌 **فرمت صحیح:**\n"
            "`1تاس 200`\n"
            "`1بسکتبال 150`\n"
            "`1بولینگ 100`\n"
            "`1دارت 300`\n\n"
            "💰 شرط باید بین **۵۰** تا **۵۰۰۰** سکه باشد."
        )
        return

    game_name = match.group(1)
    try:
        bet = int(match.group(2))
    except:
        await update.message.reply_text("❌ مقدار شرط باید عدد باشه!")
        return

    if bet < 50 or bet > 5000:
        await update.message.reply_text("❌ شرط باید بین **۵۰** تا **۵۰۰۰** سکه باشد!")
        return
    if get_balance(user_id) < bet:
        await update.message.reply_text(f"❌ موجودی کافی نداری! (موجودی: {get_balance(user_id)} سکه)")
        return

    # ========== بازی تاس ==========
    if game_name == "تاس":
        user_roll = random.randint(1, 6)
        bot_roll = random.randint(1, 6)
        if user_roll > bot_roll:
            win = bet * 2
            add_balance(user_id, win)
            update_stats(user_id, "wins")
            result = f"🎉 بردی! +{win} سکه"
        elif user_roll < bot_roll:
            add_balance(user_id, -bet)
            update_stats(user_id, "losses")
            result = f"😢 باختی! -{bet} سکه"
        else:
            update_stats(user_id, "draws")
            result = "🤝 مساوی! شرط برگشت"
        await update.message.reply_text(
            f"🎲 **بازی تاس**\n\n"
            f"🎲 تو: {user_roll}\n"
            f"🤖 ربات: {bot_roll}\n"
            f"💰 شرط: {bet} سکه\n"
            f"📌 نتیجه: {result}"
        )

    # ========== بازی بسکتبال ==========
    elif game_name == "بسکتبال":
        user_score = random.choice(["گل کردی! 🏀✅", "گل نشد! ❌"])
        if user_score == "گل کردی! 🏀✅":
            win = bet * 3
            add_balance(user_id, win)
            update_stats(user_id, "wins")
            result = f"🌟 +{win} سکه"
        else:
            add_balance(user_id, -bet)
            update_stats(user_id, "losses")
            result = f"💔 -{bet} سکه"
        await update.message.reply_text(
            f"🏀 **بازی بسکتبال**\n\n"
            f"🏀 شوت: {user_score}\n"
            f"💰 شرط: {bet} سکه\n"
            f"📌 نتیجه: {result}"
        )

    # ========== بازی بولینگ ==========
    elif game_name == "بولینگ":
        pins_down = random.randint(0, 10)
        user_guess = random.randint(0, 10)
        diff = abs(pins_down - user_guess)
        reward = max(0, bet * (10 - diff) // 10)

        if reward > bet:
            add_balance(user_id, reward - bet)
            update_stats(user_id, "wins")
            result = f"🎉 +{reward} سکه"
        elif reward < bet:
            add_balance(user_id, reward - bet)
            update_stats(user_id, "losses")
            result = f"😢 -{bet - reward} سکه"
        else:
            result = "🤝 دقیقاً شرط برگشت"
        await update.message.reply_text(
            f"🎳 **بازی بولینگ**\n\n"
            f"🎳 پین‌های خوابیده: {pins_down} / ۱۰\n"
            f"🎯 حدس تو: {user_guess}\n"
            f"💰 شرط: {bet} سکه\n"
            f"🎁 پاداش: {reward} سکه\n"
            f"📌 نتیجه: {result}"
        )

    # ========== بازی دارت ==========
    elif game_name == "دارت":
        user_throw = random.randint(1, 10)
        bot_throw = random.randint(1, 10)
        target = random.randint(1, 10)

        user_diff = abs(user_throw - target)
        bot_diff = abs(bot_throw - target)

        if user_diff < bot_diff:
            win = bet * 2
            add_balance(user_id, win)
            update_stats(user_id, "wins")
            result = f"🎯 بردی! +{win} سکه"
        elif user_diff > bot_diff:
            add_balance(user_id, -bet)
            update_stats(user_id, "losses")
            result = f"😢 باختی! -{bet} سکه"
        else:
            update_stats(user_id, "draws")
            result = "🤝 مساوی! شرط برگشت"

        await update.message.reply_text(
            f"🎯 **بازی دارت**\n\n"
            f"🎯 هدف: {target}\n"
            f"📌 پرتاب تو: {user_throw} (فاصله: {user_diff})\n"
            f"📌 پرتاب ربات: {bot_throw} (فاصله: {bot_diff})\n"
            f"💰 شرط: {bet} سکه\n"
            f"📌 نتیجه: {result}"
        )

# ========== موجودی ==========
async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    bal = get_balance(user_id)
    await update.message.reply_text(f"💰 **موجودی شما:** {bal} سکه 🪙")

# ========== آمار ==========
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    stats_data = get_stats(user_id)
    await update.message.reply_text(
        f"📊 **آمار بازی‌های شما:**\n\n"
        f"🏆 برد: {stats_data['wins']}\n"
        f"💔 باخت: {stats_data['losses']}\n"
        f"🤝 مساوی: {stats_data['draws']}"
    )

# ========== انتقال ==========
async def transfer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if len(context.args) < 2:
        await update.message.reply_text("❌ دستور: `/transfer 100 123456789`")
        return
    try:
        amount = int(context.args[0])
        target_id = int(context.args[1])
    except:
        await update.message.reply_text("❌ دستور صحیح نیست! مثال: `/transfer 100 123456789`")
        return

    user_id = update.effective_user.id
    if amount <= 0:
        await update.message.reply_text("❌ مقدار باید مثبت باشه!")
        return
    if target_id == user_id:
        await update.message.reply_text("❌ نمی‌تونی به خودت انتقال بدی!")
        return
    if get_balance(user_id) < amount:
        await update.message.reply_text("❌ موجودی کافی نداری!")
        return

    add_balance(user_id, -amount)
    add_balance(target_id, amount)
    await update.message.reply_text(f"✅ {amount} سکه به کاربر با آیدی {target_id} انتقال داده شد.")

# ========== ریست موجودی (فقط مالک) ==========
async def reset_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("❌ فقط مالک ربات می‌تونه موجودی رو ریست کنه!")
        return

    owner_balance = get_balance(OWNER_ID)
    save_data({})
    set_balance(OWNER_ID, owner_balance)
    await update.message.reply_text(f"✅ **همه موجودی‌ها به صفر رسید.** (موجودی شما: {owner_balance} سکه دست نخورده ماند) 🔄")

# ========== ریست آمار بازی‌ها (فقط مالک) ==========
async def reset_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("❌ فقط مالک ربات می‌تونه آمار رو ریست کنه!")
        return

    save_stats({})
    await update.message.reply_text("✅ **همه آمار بازی‌ها با موفقیت صفر شد.** از نو شروع می‌کنیم! 🔄")

# ========== ریست کامل (موجودی به جز مالک + آمار) ==========
async def reset_all_full(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    if user_id != OWNER_ID:
        await update.message.reply_text("❌ فقط مالک ربات می‌تونه ریست کامل انجام بده!")
        return

    owner_balance = get_balance(OWNER_ID)
    save_data({})
    set_balance(OWNER_ID, owner_balance)
    save_stats({})
    await update.message.reply_text(
        f"✅ **ریست کامل انجام شد!**\n\n"
        f"• همه موجودی‌ها به جز شما صفر شد.\n"
        f"• همه آمار بازی‌ها پاک شد.\n"
        f"• موجودی شما: {owner_balance} سکه دست نخورده ماند. 🔄"
    )

# ========== مدیریت دکمه‌های شیشه‌ای ==========
async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    data = query.data
    if data == "game_dice":
        await query.message.reply_text("🎲 مثال: `1تاس 200`")
    elif data == "game_basketball":
        await query.message.reply_text("🏀 مثال: `1بسکتبال 150`")
    elif data == "game_bowling":
        await query.message.reply_text("🎳 مثال: `1بولینگ 100`")
    elif data == "game_dart":
        await query.message.reply_text("🎯 مثال: `1دارت 300`")
    elif data == "balance":
        user_id = query.from_user.id
        bal = get_balance(user_id)
        await query.message.reply_text(f"💰 **موجودی شما:** {bal} سکه 🪙")
    elif data == "stats":
        user_id = query.from_user.id
        stats_data = get_stats(user_id)
        await query.message.reply_text(
            f"📊 **آمار بازی‌های شما:**\n\n"
            f"🏆 برد: {stats_data['wins']}\n"
            f"💔 باخت: {stats_data['losses']}\n"
            f"🤝 مساوی: {stats_data['draws']}"
        )

# ========== اجرا ==========
def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("transfer", transfer))
    app.add_handler(CommandHandler("reset", reset_all))
    app.add_handler(CommandHandler("resetstats", reset_stats))
    app.add_handler(CommandHandler("resetall", reset_all_full))
    app.add_handler(CallbackQueryHandler(button_handler))

    # هندلر برای دستورات 1بازی
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_game_command))

    print("🤖 ربات روشن شد...")
    app.run_polling()

if __name__ == "__main__":
    main()
