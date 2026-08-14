import json
import os
import random
import re
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# ========== لاگ‌گیری ==========
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# ========== تنظیمات ==========
TOKEN = "8981045477:AAHCiu01fynQ0mkwCTS_W4wlnIZfawdlzLM"
OWNER_ID = 123456789  # <-- آیدی عددی خودت رو از @userinfobot بگیر
OWNER_BALANCE = 50000000  # موجودی مالک (۵۰ میلیون)

DATA_FILE = "balances.json"
STATS_FILE = "stats.json"

# ========== توابع موجودی ==========
def load_data():
    if not os.path.exists(DATA_FILE):
        return {}
    try:
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_balance(user_id):
    data = load_data()
    uid = str(user_id)
    
    # اگر کاربر مالک است و موجودی ندارد، ۵۰ میلیون تنظیم کن
    if user_id == OWNER_ID:
        if uid not in data or data[uid] == 0:
            data[uid] = OWNER_BALANCE
            save_data(data)
        return data.get(uid, OWNER_BALANCE)
    
    return data.get(uid, 0)

def set_balance(user_id, amount):
    data = load_data()
    uid = str(user_id)
    
    # اگر کاربر مالک است، اجازه نده موجودی از ۵۰ میلیون کمتر بشه (اختیاری)
    # ولی برای انعطاف، این خط رو کامنت می‌ذارم:
    # if user_id == OWNER_ID and amount < OWNER_BALANCE:
    #     amount = OWNER_BALANCE
    
    data[uid] = amount
    save_data(data)

def add_balance(user_id, amount):
    current = get_balance(user_id)
    new_balance = current + amount
    if new_balance < 0:
        new_balance = 0
    set_balance(user_id, new_balance)
    return new_balance

# ========== توابع آمار ==========
def load_stats():
    if not os.path.exists(STATS_FILE):
        return {}
    try:
        with open(STATS_FILE, "r") as f:
            return json.load(f)
    except:
        return {}

def save_stats(data):
    with open(STATS_FILE, "w") as f:
        json.dump(data, f, indent=4)

def get_stats(user_id):
    data = load_stats()
    return data.get(str(user_id), {"wins": 0, "losses": 0, "draws": 0})

def update_stats(user_id, result):
    data = load_stats()
    uid = str(user_id)
    if uid not in data:
        data[uid] = {"wins": 0, "losses": 0, "draws": 0}
    data[uid][result] += 1
    save_stats(data)

# ========== صفحه کلید شیشه‌ای ==========
def get_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎲 تاس", callback_data="dice")],
        [InlineKeyboardButton("🏀 بسکتبال", callback_data="basketball")],
        [InlineKeyboardButton("🎳 بولینگ", callback_data="bowling")],
        [InlineKeyboardButton("🎯 دارت", callback_data="dart")],
        [InlineKeyboardButton("💰 موجودی", callback_data="balance")],
        [InlineKeyboardButton("📊 آمار", callback_data="stats")],
    ])

# ========== دستور start ==========
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        await update.message.reply_text(
            "🎮 **به ربات بازی خوش اومدی!**\n\n"
            "📌 **فرمت بازی:**\n"
            "`1تاس 200`\n"
            "`1بسکتبال 150`\n"
            "`1بولینگ 100`\n"
            "`1دارت 300`\n\n"
            "💰 شرط: **۵۰** تا **۵۰۰۰** سکه\n"
            "📊 آمار برد/باخت/مساوی ذخیره میشه\n\n"
            "📌 **سایر دستورات:**\n"
            "`/balance` - موجودی\n"
            "`/stats` - آمار\n"
            "`/transfer 100 123456789` - انتقال سکه\n"
            "`/reset` - ریست موجودی (فقط مالک)\n"
            "`/resetstats` - ریست آمار (فقط مالک)\n"
            "`/resetall` - ریست کامل (فقط مالک)",
            reply_markup=get_keyboard()
        )
    except Exception as e:
        logger.error(f"start error: {e}")
        await update.message.reply_text(f"❌ خطا: {e}")

# ========== پردازش بازی‌ها ==========
async def handle_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        text = update.message.text.strip()
        user_id = update.effective_user.id

        pattern = r'^1(تاس|بسکتبال|بولینگ|دارت)\s+(\d+)$'
        match = re.match(pattern, text)

        if not match:
            await update.message.reply_text(
                "❌ **فرمت اشتباه!**\n\n"
                "📌 **فرمت صحیح:**\n"
                "`1تاس 200`\n"
                "`1بسکتبال 150`\n"
                "`1بولینگ 100`\n"
                "`1دارت 300`"
            )
            return

        game_name = match.group(1)
        bet = int(match.group(2))

        if bet < 50 or bet > 5000:
            await update.message.reply_text("❌ شرط باید بین **۵۰** تا **۵۰۰۰** سکه باشد!")
            return

        balance = get_balance(user_id)
        if balance < bet:
            await update.message.reply_text(f"❌ موجودی کافی نیست! (موجودی: {balance} سکه)")
            return

        # ===== بازی تاس =====
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
                result = "🤝 مساوی!"
            await update.message.reply_text(
                f"🎲 **تاس**\n\n"
                f"🎲 تو: {user_roll}\n"
                f"🤖 ربات: {bot_roll}\n"
                f"💰 شرط: {bet} سکه\n"
                f"📌 {result}"
            )

        # ===== بازی بسکتبال =====
        elif game_name == "بسکتبال":
            if random.choice([True, False]):
                win = bet * 3
                add_balance(user_id, win)
                update_stats(user_id, "wins")
                result = f"🌟 +{win} سکه"
            else:
                add_balance(user_id, -bet)
                update_stats(user_id, "losses")
                result = f"💔 -{bet} سکه"
            await update.message.reply_text(
                f"🏀 **بسکتبال**\n\n"
                f"🏀 شوت: {'گل کردی! ✅' if 'برد' in result else 'گل نشد! ❌'}\n"
                f"💰 شرط: {bet} سکه\n"
                f"📌 {result}"
            )

        # ===== بازی بولینگ =====
        elif game_name == "بولینگ":
            pins = random.randint(0, 10)
            guess = random.randint(0, 10)
            diff = abs(pins - guess)
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
                result = "🤝 شرط برگشت"
            await update.message.reply_text(
                f"🎳 **بولینگ**\n\n"
                f"🎳 پین‌ها: {pins}\n"
                f"🎯 حدس تو: {guess}\n"
                f"🎁 پاداش: {reward} سکه\n"
                f"📌 {result}"
            )

        # ===== بازی دارت =====
        elif game_name == "دارت":
            target = random.randint(1, 10)
            user_throw = random.randint(1, 10)
            bot_throw = random.randint(1, 10)

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
                result = "🤝 مساوی!"
            await update.message.reply_text(
                f"🎯 **دارت**\n\n"
                f"🎯 هدف: {target}\n"
                f"📌 تو: {user_throw} (فاصله: {user_diff})\n"
                f"📌 ربات: {bot_throw} (فاصله: {bot_diff})\n"
                f"💰 شرط: {bet} سکه\n"
                f"📌 {result}"
            )

    except Exception as e:
        logger.error(f"handle_game error: {e}")
        await update.message.reply_text(f"❌ خطای داخلی: {e}")

# ========== موجودی ==========
async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        bal = get_balance(user_id)
        await update.message.reply_text(f"💰 **موجودی شما:** {bal:,} سکه")
    except Exception as e:
        logger.error(f"balance error: {e}")
        await update.message.reply_text(f"❌ خطا: {e}")

# ========== آمار ==========
async def stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        user_id = update.effective_user.id
        s = get_stats(user_id)
        await update.message.reply_text(
            f"📊 **آمار شما:**\n\n"
            f"🏆 برد: {s['wins']}\n"
            f"💔 باخت: {s['losses']}\n"
            f"🤝 مساوی: {s['draws']}"
        )
    except Exception as e:
        logger.error(f"stats error: {e}")
        await update.message.reply_text(f"❌ خطا: {e}")

# ========== انتقال موجودی ==========
async def transfer(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if len(context.args) < 2:
            await update.message.reply_text(
                "❌ **دستور:** `/transfer مقدار آیدی_کاربر`\n\n"
                "مثال: `/transfer 100 123456789`\n"
                "📌 آیدی کاربر رو از `@userinfobot` بگیر."
            )
            return

        amount = int(context.args[0])
        target_id = int(context.args[1])
        user_id = update.effective_user.id

        if amount <= 0:
            await update.message.reply_text("❌ مقدار باید بیشتر از ۰ باشد!")
            return

        if target_id == user_id:
            await update.message.reply_text("❌ نمی‌تونی به خودت انتقال بدی!")
            return

        if get_balance(user_id) < amount:
            await update.message.reply_text(f"❌ موجودی کافی نیست! (موجودی: {get_balance(user_id):,} سکه)")
            return

        # انجام انتقال
        add_balance(user_id, -amount)
        add_balance(target_id, amount)

        await update.message.reply_text(
            f"✅ **انتقال انجام شد!**\n\n"
            f"💰 {amount:,} سکه به کاربر با آیدی `{target_id}` انتقال داده شد.\n"
            f"📌 موجودی جدید شما: {get_balance(user_id):,} سکه"
        )
    except ValueError:
        await update.message.reply_text("❌ مقدار و آیدی باید عدد باشند!\nمثال: `/transfer 100 123456789`")
    except Exception as e:
        logger.error(f"transfer error: {e}")
        await update.message.reply_text(f"❌ خطا: {e}")

# ========== ریست موجودی ==========
async def reset(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.effective_user.id != OWNER_ID:
            await update.message.reply_text("❌ فقط مالک ربات!")
            return
        # موجودی مالک رو ۵۰ میلیون بذار
        save_data({})
        set_balance(OWNER_ID, OWNER_BALANCE)
        await update.message.reply_text(f"✅ موجودی همه به جز شما ریست شد! (موجودی شما: {OWNER_BALANCE:,} سکه)")
    except Exception as e:
        logger.error(f"reset error: {e}")
        await update.message.reply_text(f"❌ خطا: {e}")

# ========== ریست آمار ==========
async def reset_stats(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.effective_user.id != OWNER_ID:
            await update.message.reply_text("❌ فقط مالک ربات!")
            return
        save_stats({})
        await update.message.reply_text("✅ آمار همه ریست شد!")
    except Exception as e:
        logger.error(f"reset_stats error: {e}")
        await update.message.reply_text(f"❌ خطا: {e}")

# ========== ریست کامل ==========
async def reset_all(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        if update.effective_user.id != OWNER_ID:
            await update.message.reply_text("❌ فقط مالک ربات!")
            return
        save_data({})
        set_balance(OWNER_ID, OWNER_BALANCE)
        save_stats({})
        await update.message.reply_text(f"✅ ریست کامل شد! (موجودی شما: {OWNER_BALANCE:,} سکه)")
    except Exception as e:
        logger.error(f"reset_all error: {e}")
        await update.message.reply_text(f"❌ خطا: {e}")

# ========== دکمه‌های شیشه‌ای ==========
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    try:
        query = update.callback_query
        await query.answer()

        data = query.data
        if data in ["dice", "basketball", "bowling", "dart"]:
            names = {"dice": "تاس", "basketball": "بسکتبال", "bowling": "بولینگ", "dart": "دارت"}
            await query.message.reply_text(f"🎮 مثال: `1{names[data]} 200`")
        elif data == "balance":
            user_id = query.from_user.id
            await query.message.reply_text(f"💰 موجودی: {get_balance(user_id):,} سکه")
        elif data == "stats":
            user_id = query.from_user.id
            s = get_stats(user_id)
            await query.message.reply_text(
                f"📊 آمار:\n"
                f"🏆 برد: {s['wins']}\n"
                f"💔 باخت: {s['losses']}\n"
                f"🤝 مساوی: {s['draws']}"
            )
    except Exception as e:
        logger.error(f"button error: {e}")
        await query.message.reply_text(f"❌ خطا: {e}")

# ========== اجرا ==========
def main():
    try:
        app = Application.builder().token(TOKEN).build()

        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("balance", balance))
        app.add_handler(CommandHandler("stats", stats))
        app.add_handler(CommandHandler("transfer", transfer))
        app.add_handler(CommandHandler("reset", reset))
        app.add_handler(CommandHandler("resetstats", reset_stats))
        app.add_handler(CommandHandler("resetall", reset_all))
        app.add_handler(CallbackQueryHandler(button))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_game))

        print("🤖 ربات روشن شد...")
        app.run_polling()
    except Exception as e:
        print(f"❌ خطا در اجرا: {e}")

if __name__ == "__main__":
    main()
