import json
import os
import random
import re
import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TOKEN = "8981045477:AAHCiu01fynQ0mkwCTS_W4wlnIZfawdlzLM"
OWNER_ID = 8552447077
OWNER_BALANCE = 50_000_000

DATA_FILE = "balances.json"
STATS_FILE = "stats.json"

# ایموجی‌های تاس
DICE_EMOJIS = ["⚀", "⚁", "⚂", "⚃", "⚄", "⚅"]

def load_data():
    if not os.path.exists(DATA_FILE): return {}
    with open(DATA_FILE, "r") as f: return json.load(f)

def save_data(d):
    with open(DATA_FILE, "w") as f: json.dump(d, f, indent=4)

def get_balance(uid):
    data = load_data()
    uid = str(uid)
    if int(uid) == OWNER_ID and uid not in data:
        data[uid] = OWNER_BALANCE
        save_data(data)
    return data.get(uid, 0)

def set_balance(uid, amt):
    data = load_data()
    data[str(uid)] = amt
    save_data(data)

def add_balance(uid, amt):
    set_balance(uid, get_balance(uid) + amt)

def load_stats():
    if not os.path.exists(STATS_FILE): return {}
    with open(STATS_FILE, "r") as f: return json.load(f)

def save_stats(d):
    with open(STATS_FILE, "w") as f: json.dump(d, f, indent=4)

def get_stats(uid):
    return load_stats().get(str(uid), {"wins":0, "losses":0, "draws":0})

def update_stats(uid, res):
    d = load_stats()
    uid = str(uid)
    if uid not in d: d[uid] = {"wins":0, "losses":0, "draws":0}
    d[uid][res] += 1
    save_stats(d)

def get_keyboard():
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🎲 تاس", callback_data="dice")],
        [InlineKeyboardButton("🏀 بسکتبال", callback_data="basketball")],
        [InlineKeyboardButton("🎳 بولینگ", callback_data="bowling")],
        [InlineKeyboardButton("🎯 دارت", callback_data="dart")],
        [InlineKeyboardButton("💰 موجودی", callback_data="balance")],
        [InlineKeyboardButton("📊 آمار", callback_data="stats")],
    ])

async def start(update, context):
    await update.message.reply_text(
        "🎮 **به ربات بازی خوش اومدی!**\n\n"
        "📌 **فرمت بازی:**\n"
        "`1تاس 200`\n`1بسکتبال 150`\n`1بولینگ 100`\n`1دارت 300`\n\n"
        "💰 شرط: **۵۰** تا **۵۰۰۰** سکه\n\n"
        "📌 **دستورات:**\n"
        "/balance - موجودی\n/stats - آمار\n"
        "/transfer 100 123456789 - انتقال سکه\n"
        "/reset - ریست موجودی (مالک)\n/resetstats - ریست آمار (مالک)\n/resetall - ریست کامل (مالک)",
        reply_markup=get_keyboard()
    )

async def handle_game(update, context):
    try:
        text = update.message.text.strip()
        uid = update.effective_user.id
        
        pattern = r'^1(تاس|بسکتبال|بولینگ|دارت)\s*(\d+)$'
        match = re.match(pattern, text)
        
        if not match:
            await update.message.reply_text(
                "❌ **فرمت اشتباه!**\n\n"
                "📌 **فرمت صحیح:**\n"
                "`1تاس 200` یا `1تاس200`\n"
                "`1بسکتبال 150` یا `1بسکتبال150`\n"
                "`1بولینگ 100` یا `1بولینگ100`\n"
                "`1دارت 300` یا `1دارت300`"
            )
            return
            
        game_name = match.group(1)
        bet = int(match.group(2))
        
        if bet < 50 or bet > 5000:
            await update.message.reply_text("❌ شرط باید بین **۵۰** تا **۵۰۰۰** سکه باشد!")
            return
            
        if get_balance(uid) < bet:
            await update.message.reply_text(f"❌ موجودی کافی نیست! (موجودی: {get_balance(uid)})")
            return

        # ==================== بازی تاس ====================
        if game_name == "تاس":
            user_roll = random.randint(1, 6)  # اول کاربر
            bot_roll = random.randint(1, 6)   # بعد ربات
            
            user_emoji = DICE_EMOJIS[user_roll - 1]
            bot_emoji = DICE_EMOJIS[bot_roll - 1]
            
            if user_roll > bot_roll:
                add_balance(uid, bet*2)
                update_stats(uid, "wins")
                result = f"🎉 بردی! +{bet*2} سکه"
            elif user_roll < bot_roll:
                add_balance(uid, -bet)
                update_stats(uid, "losses")
                result = f"😢 باختی! -{bet} سکه"
            else:
                update_stats(uid, "draws")
                result = "🤝 مساوی! شرط برگشت"
            
            await update.message.reply_text(
                f"🎲 **بازی تاس**\n\n"
                f"🎲 **پرتاب تو:** {user_emoji}  ({user_roll})\n"
                f"🎲 **پرتاب ربات:** {bot_emoji}  ({bot_roll})\n"
                f"💰 شرط: {bet} سکه\n"
                f"📌 {result}"
            )

        # ==================== بازی بسکتبال ====================
        elif game_name == "بسکتبال":
            user_score = random.choice(["🏀 گل کردی! ✅", "🏀 گل نشد! ❌"])  # اول کاربر
            bot_score = random.choice(["🏀 گل کردی! ✅", "🏀 گل نشد! ❌"])   # بعد ربات
            
            if user_score == "🏀 گل کردی! ✅" and bot_score == "🏀 گل نشد! ❌":
                add_balance(uid, bet*3)
                update_stats(uid, "wins")
                result = f"🌟 +{bet*3} سکه"
            elif user_score == "🏀 گل نشد! ❌" and bot_score == "🏀 گل کردی! ✅":
                add_balance(uid, -bet)
                update_stats(uid, "losses")
                result = f"💔 -{bet} سکه"
            else:
                update_stats(uid, "draws")
                result = "🤝 مساوی! شرط برگشت"
            
            await update.message.reply_text(
                f"🏀 **بازی بسکتبال**\n\n"
                f"🏀 **شوت تو:** {user_score}\n"
                f"🏀 **شوت ربات:** {bot_score}\n"
                f"💰 شرط: {bet} سکه\n"
                f"📌 {result}"
            )

        # ==================== بازی بولینگ ====================
        elif game_name == "بولینگ":
            user_pins = random.randint(0, 10)  # اول کاربر
            bot_pins = random.randint(0, 10)   # بعد ربات
            
            if user_pins > bot_pins:
                win = bet * 2
                add_balance(uid, win)
                update_stats(uid, "wins")
                result = f"🎉 بردی! +{win} سکه"
            elif user_pins < bot_pins:
                add_balance(uid, -bet)
                update_stats(uid, "losses")
                result = f"😢 باختی! -{bet} سکه"
            else:
                update_stats(uid, "draws")
                result = "🤝 مساوی! شرط برگشت"
            
            await update.message.reply_text(
                f"🎳 **بازی بولینگ**\n\n"
                f"🎳 **پین‌های تو:** {user_pins} / ۱۰\n"
                f"🎳 **پین‌های ربات:** {bot_pins} / ۱۰\n"
                f"💰 شرط: {bet} سکه\n"
                f"📌 {result}"
            )

        # ==================== بازی دارت ====================
        elif game_name == "دارت":
            target = random.randint(1, 10)          # هدف مشترک
            user_throw = random.randint(1, 10)      # اول کاربر
            bot_throw = random.randint(1, 10)       # بعد ربات
            
            user_diff = abs(user_throw - target)
            bot_diff = abs(bot_throw - target)
            
            if user_diff < bot_diff:
                win = bet * 2
                add_balance(uid, win)
                update_stats(uid, "wins")
                result = f"🎯 بردی! +{win} سکه"
            elif user_diff > bot_diff:
                add_balance(uid, -bet)
                update_stats(uid, "losses")
                result = f"😢 باختی! -{bet} سکه"
            else:
                update_stats(uid, "draws")
                result = "🤝 مساوی! شرط برگشت"
            
            await update.message.reply_text(
                f"🎯 **بازی دارت**\n\n"
                f"🎯 **هدف:** {target}\n"
                f"🎯 **پرتاب تو:** {user_throw} (فاصله: {user_diff})\n"
                f"🎯 **پرتاب ربات:** {bot_throw} (فاصله: {bot_diff})\n"
                f"💰 شرط: {bet} سکه\n"
                f"📌 {result}"
            )

    except Exception as e:
        logger.error(f"handle_game error: {e}")
        await update.message.reply_text(f"❌ خطا: {e}")

async def balance(update, context):
    await update.message.reply_text(f"💰 موجودی: {get_balance(update.effective_user.id):,} سکه")

async def stats(update, context):
    s = get_stats(update.effective_user.id)
    await update.message.reply_text(f"📊 برد: {s['wins']}\nباخت: {s['losses']}\nمساوی: {s['draws']}")

async def transfer(update, context):
    try:
        if len(context.args) < 2:
            await update.message.reply_text("❌ /transfer 100 123456789")
            return
        amt = int(context.args[0])
        tid = int(context.args[1])
        uid = update.effective_user.id
        if amt <= 0 or tid == uid or get_balance(uid) < amt:
            await update.message.reply_text("❌ خطا")
            return
        add_balance(uid, -amt)
        add_balance(tid, amt)
        await update.message.reply_text(f"✅ {amt:,} سکه منتقل شد")
    except Exception as e:
        logger.error(f"transfer error: {e}")
        await update.message.reply_text(f"❌ خطا: {e}")

async def reset(update, context):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ فقط مالک")
        return
    save_data({})
    set_balance(OWNER_ID, OWNER_BALANCE)
    await update.message.reply_text(f"✅ موجودی ریست شد (موجودی شما: {OWNER_BALANCE:,})")

async def resetstats(update, context):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ فقط مالک")
        return
    save_stats({})
    await update.message.reply_text("✅ آمار ریست شد")

async def resetall(update, context):
    if update.effective_user.id != OWNER_ID:
        await update.message.reply_text("❌ فقط مالک")
        return
    save_data({})
    set_balance(OWNER_ID, OWNER_BALANCE)
    save_stats({})
    await update.message.reply_text(f"✅ ریست کامل شد (موجودی شما: {OWNER_BALANCE:,})")

async def button(update, context):
    try:
        q = update.callback_query
        await q.answer()
        cmd = q.data
        if cmd in ["dice","basketball","bowling","dart"]:
            names = {"dice":"تاس", "basketball":"بسکتبال", "bowling":"بولینگ", "dart":"دارت"}
            await q.message.reply_text(f"🎮 مثال: `1{names[cmd]} 200` یا `1{names[cmd]}200`")
        elif cmd == "balance":
            await q.message.reply_text(f"💰 موجودی: {get_balance(q.from_user.id):,} سکه")
        elif cmd == "stats":
            s = get_stats(q.from_user.id)
            await q.message.reply_text(f"📊 برد: {s['wins']}\nباخت: {s['losses']}\nمساوی: {s['draws']}")
    except Exception as e:
        logger.error(f"button error: {e}")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("transfer", transfer))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("resetstats", resetstats))
    app.add_handler(CommandHandler("resetall", resetall))
    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_game))
    print("🤖 ربات روشن شد...")
    app.run_polling()

if __name__ == "__main__":
    main() 
