import json, os, random, re, logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

TOKEN = "8981045477:AAHCiu01fynQ0mkwCTS_W4wlnIZfawdlzLM"
OWNER_ID = 8552447077
OWNER_BALANCE = 50_000_000

DATA_FILE = "balances.json"
STATS_FILE = "stats.json"

def load_data():
    if not os.path.exists(DATA_FILE): return {}
    with open(DATA_FILE, "r") as f: return json.load(f)
def save_data(d):
    with open(DATA_FILE, "w") as f: json.dump(d, f, indent=4)
def get_balance(uid):
    data = load_data()
    uid = str(uid)

    if int(uid) == OWNER_ID:
        if data.get(uid) != OWNER_BALANCE:
            data[uid] = OWNER_BALANCE
            save_data(data)
        return OWNER_BALANCE

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
    d = load_stats(); uid = str(uid)
    if uid not in d: d[uid] = {"wins":0, "losses":0, "draws":0}
    d[uid][res] += 1; save_stats(d)

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
    text = update.message.text.strip()
    uid = update.effective_user.id
    match = re.match(r'^1(تاس|بسکتبال|بولینگ|دارت)\s+(\d+)$', text)
    if not match:
        await update.message.reply_text("❌ مثال: `1تاس 200`")
        return
    game, bet = match.group(1), int(match.group(2))
    if bet < 50 or bet > 5000:
        await update.message.reply_text("❌ شرط باید ۵۰ تا ۵۰۰۰ باشد")
        return
    if get_balance(uid) < bet:
        await update.message.reply_text(f"❌ موجودی کافی نیست! (موجودی: {get_balance(uid)})")
        return

    if game == "تاس":
        u, b = random.randint(1,6), random.randint(1,6)
        if u > b:
            add_balance(uid, bet*2); update_stats(uid, "wins"); res = f"🎉 برد! +{bet*2}"
        elif u < b:
            add_balance(uid, -bet); update_stats(uid, "losses"); res = f"😢 باخت! -{bet}"
        else:
            update_stats(uid, "draws"); res = "🤝 مساوی"
        await update.message.reply_text(f"🎲 تاس\nتو: {u}\nربات: {b}\n{res}")
    elif game == "بسکتبال":
        if random.choice([True, False]):
            add_balance(uid, bet*3); update_stats(uid, "wins"); res = f"🌟 +{bet*3}"
        else:
            add_balance(uid, -bet); update_stats(uid, "losses"); res = f"💔 -{bet}"
        await update.message.reply_text(f"🏀 بسکتبال\n{res}")
    elif game == "بولینگ":
        pins, guess = random.randint(0,10), random.randint(0,10)
        reward = max(0, bet * (10 - abs(pins-guess)) // 10)
        if reward > bet:
            add_balance(uid, reward - bet); update_stats(uid, "wins"); res = f"🎉 +{reward}"
        elif reward < bet:
            add_balance(uid, reward - bet); update_stats(uid, "losses"); res = f"😢 -{bet-reward}"
        else:
            res = "🤝 برگشت شرط"
        await update.message.reply_text(f"🎳 بولینگ\nپین‌ها: {pins}\nحدس: {guess}\nپاداش: {reward}\n{res}")
    elif game == "دارت":
        target, u, b = random.randint(1,10), random.randint(1,10), random.randint(1,10)
        if abs(u-target) < abs(b-target):
            add_balance(uid, bet*2); update_stats(uid, "wins"); res = f"🎯 +{bet*2}"
        elif abs(u-target) > abs(b-target):
            add_balance(uid, -bet); update_stats(uid, "losses"); res = f"😢 -{bet}"
        else:
            update_stats(uid, "draws"); res = "🤝 مساوی"
        await update.message.reply_text(f"🎯 دارت\nهدف: {target}\nتو: {u}\nربات: {b}\n{res}")

async def balance(update, context):
    await update.message.reply_text(f"💰 موجودی: {get_balance(update.effective_user.id):,} سکه")

async def stats(update, context):
    s = get_stats(update.effective_user.id)
    await update.message.reply_text(f"📊 برد: {s['wins']}\nباخت: {s['losses']}\nمساوی: {s['draws']}")

async def transfer(update, context):
    if len(context.args) < 2:
        await update.message.reply_text("❌ /transfer 100 123456789")
        return
    amt, tid = int(context.args[0]), int(context.args[1])
    uid = update.effective_user.id
    if amt <= 0 or tid == uid or get_balance(uid) < amt:
        await update.message.reply_text("❌ خطا")
        return
    add_balance(uid, -amt); add_balance(tid, amt)
    await update.message.reply_text(f"✅ {amt:,} سکه منتقل شد")

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
    q = update.callback_query; await q.answer()
    cmd = q.data
    if cmd in ["dice","basketball","bowling","dart"]:
        names = {"dice":"تاس", "basketball":"بسکتبال", "bowling":"بولینگ", "dart":"دارت"}
        await q.message.reply_text(f"🎮 مثال: `1{names[cmd]} 200`")
    elif cmd == "balance":
        await q.message.reply_text(f"💰 موجودی: {get_balance(q.from_user.id):,} سکه")
    elif cmd == "stats":
        s = get_stats(q.from_user.id)
        await q.message.reply_text(f"📊 برد: {s['wins']}\nباخت: {s['losses']}\nمساوی: {s['draws']}")

def main():
async def myid(update, context):
    await update.message.reply_text(
        f"ID شما: {update.effective_user.id}"
    )
def main():
    def myid(update, context):
    return update.message.reply_text(
        f"ID شما: {update.effective_user.id}"
    )


def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("balance", balance))
    app.add_handler(CommandHandler("stats", stats))
    app.add_handler(CommandHandler("transfer", transfer))
    app.add_handler(CommandHandler("reset", reset))
    app.add_handler(CommandHandler("resetstats", resetstats))
    app.add_handler(CommandHandler("resetall", resetall))
    app.add_handler(CommandHandler("myid", myid))

    app.add_handler(CallbackQueryHandler(button))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_game))

    print("🤖 ربات روشن شد...")
    app.run_polling()


if __name__ == "__main__":
    main()
