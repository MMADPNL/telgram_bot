import logging
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

# ======== اطلاعات شما ========
ADMIN_ID = 8552447077  # ایدی عددی شما
TOKEN = "8981045477:AAHCiu01fynQ0mkwCTS_W4wlnIZfawdlzLM"  # توکن ربات

user_data = {}

def get_user(user_id):
    if user_id not in user_data:
        user_data[user_id] = {'balance': 0, 'bet_choice': None, 'secret': None}
    return user_data[user_id]

def get_balance(user_id):
    return get_user(user_id)['balance']

def change_balance(user_id, amount):
    user = get_user(user_id)
    user['balance'] = max(0, user['balance'] + amount)
    return user['balance']

# ======== منوی اصلی ========
async def main_menu(update, context, text=None):
    user_id = update.effective_user.id
    bal = get_balance(user_id)
    keyboard = [
        [InlineKeyboardButton("🎲 تاس", callback_data='dice')],
        [InlineKeyboardButton("💰 شرط‌بندی", callback_data='bet')],
        [InlineKeyboardButton("🎯 حدس عدد", callback_data='guess')],
        [InlineKeyboardButton("📊 موجودی", callback_data='balance')],
        [InlineKeyboardButton("❓ راهنما", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    msg = text or f"🎮 خوش اومدی!\n💰 سکه‌های تو: {bal}"
    if update.callback_query:
        await update.callback_query.message.edit_text(msg, reply_markup=reply_markup)
        await update.callback_query.answer()
    else:
        await update.message.reply_text(msg, reply_markup=reply_markup)

async def start(update, context):
    await main_menu(update, context)

async def help_cmd(update, context):
    await main_menu(update, context, text="🎮 بازی‌ها: تاس، شرط‌بندی، حدس عدد\n\n💸 انتقال سکه: /transfer [مبلغ] [آیدی کاربر]\nمثال: /transfer 100 8552447077")

# ======== بازی تاس ========
async def dice_game(update, context):
    user_id = update.effective_user.id
    num = random.randint(1, 6)
    emojis = {1:'⚀',2:'⚁',3:'⚂',4:'⚃',5:'⚄',6:'⚅'}
    text = f"🎲 {emojis[num]}  عدد {num}"
    if num == 6:
        change_balance(user_id, 100)
        text += "\n🎉 +۱۰۰ سکه پاداش!"
    await update.callback_query.message.edit_text(text)
    await update.callback_query.answer()
    context.job_queue.run_once(lambda ctx: main_menu(ctx.job.data, ctx), 3, data=update)

# ======== شرط‌بندی ========
async def bet_menu(update, context):
    keyboard = [
        [InlineKeyboardButton("زوج", callback_data='bet_even')],
        [InlineKeyboardButton("فرد", callback_data='bet_odd')],
        [InlineKeyboardButton("🔙 برگشت", callback_data='back')]
    ]
    await update.callback_query.message.edit_text(
        f"💰 شرط ببند (سکه: {get_balance(update.effective_user.id)})",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    await update.callback_query.answer()

async def bet_choice(update, context):
    user_id = update.effective_user.id
    get_user(user_id)['bet_choice'] = update.callback_query.data
    await update.callback_query.message.reply_text("💰 مبلغ شرط رو عدد وارد کن (حداقل ۱۰۰):")
    await update.callback_query.answer()
    context.user_data['awaiting_bet'] = True

async def handle_bet(update, context):
    if not context.user_data.get('awaiting_bet'):
        return
    user_id = update.effective_user.id
    try:
        amount = int(update.message.text)
    except:
        await update.message.reply_text("❌ عدد معتبر وارد کن!")
        return
    if amount < 100:
        await update.message.reply_text("❌ حداقل ۱۰۰ سکه")
        return
    if amount > get_balance(user_id):
        await update.message.reply_text("❌ سکه کافی نداری!")
        return

    num = random.randint(1, 6)
    is_even = num % 2 == 0
    choice = get_user(user_id).get('bet_choice', 'bet_even')
    user_even = (choice == 'bet_even')
    win = (is_even and user_even) or (not is_even and not user_even)

    if win:
        change_balance(user_id, amount * 2)
        result = f"🎉 بردی! {amount*2} سکه"
    else:
        change_balance(user_id, -amount)
        result = f"😢 باختی! {amount} سکه"

    emojis = {1:'⚀',2:'⚁',3:'⚂',4:'⚃',5:'⚄',6:'⚅'}
    await update.message.reply_text(f"🎲 {emojis[num]}  عدد {num}\n{result}\n💰 سکه: {get_balance(user_id)}")
    context.user_data['awaiting_bet'] = False
    await main_menu(update, context)

# ======== حدس عدد ========
async def guess_menu(update, context):
    user_id = update.effective_user.id
    get_user(user_id)['secret'] = random.randint(1, 10)
    await update.callback_query.message.reply_text("🎯 مبلغ شرط رو عدد وارد کن (حداقل ۱۰۰):")
    await update.callback_query.answer()
    context.user_data['awaiting_guess_amount'] = True

async def handle_guess(update, context):
    if not context.user_data.get('awaiting_guess_amount'):
        return
    user_id = update.effective_user.id
    try:
        amount = int(update.message.text)
    except:
        await update.message.reply_text("❌ عدد معتبر وارد کن!")
        return
    if amount < 100:
        await update.message.reply_text("❌ حداقل ۱۰۰ سکه")
        return
    if amount > get_balance(user_id):
        await update.message.reply_text("❌ سکه کافی نداری!")
        return

    context.user_data['guess_amount'] = amount
    context.user_data['awaiting_guess_amount'] = False
    context.user_data['awaiting_guess_number'] = True
    await update.message.reply_text("🎯 حالا عدد ۱ تا ۱۰ رو حدس بزن:")

async def handle_guess_number(update, context):
    if not context.user_data.get('awaiting_guess_number'):
        return
    user_id = update.effective_user.id
    try:
        guess = int(update.message.text)
        if guess < 1 or guess > 10:
            await update.message.reply_text("❌ عدد بین ۱ تا ۱۰ باشه!")
            return
    except:
        await update.message.reply_text("❌ عدد معتبر وارد کن!")
        return

    secret = get_user(user_id).get('secret', random.randint(1,10))
    amount = context.user_data.get('guess_amount', 100)
    diff = abs(guess - secret)

    if diff == 0:
        win = amount * 5
        change_balance(user_id, win)
        result = f"🎯 دقیق! {win} سکه بردی!"
    elif diff == 1:
        win = amount * 2
        change_balance(user_id, win)
        result = f"👏 نزدیک! {win} سکه بردی!"
    else:
        change_balance(user_id, -amount)
        result = f"😢 عدد من {secret} بود. {amount} سکه باختی."

    await update.message.reply_text(f"{result}\n💰 سکه: {get_balance(user_id)}")
    context.user_data['awaiting_guess_number'] = False
    context.user_data['guess_amount'] = 0
    await main_menu(update, context)

# ======== نمایش موجودی ========
async def show_balance(update, context):
    user_id = update.effective_user.id
    keyboard = [[InlineKeyboardButton("🔙 برگشت", callback_data='back')]]
    await update.callback_query.message.edit_text(
        f"💰 سکه‌های تو: {get_balance(user_id)}",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )
    await update.callback_query.answer()

async def back(update, context):
    await main_menu(update, context)

# ======== انتقال سکه ========
async def transfer_coin(update, context):
    user_id = update.effective_user.id
    
    # بررسی تعداد آرگومان‌ها
    if len(context.args) != 2:
        await update.message.reply_text("❌ دستور: /transfer [مبلغ] [آیدی کاربر]\nمثال: /transfer 100 8552447077")
        return
    
    try:
        amount = int(context.args[0])
        target_id = int(context.args[1])
    except ValueError:
        await update.message.reply_text("❌ لطفاً مبلغ و آیدی رو به درستی وارد کن!\nمثال: /transfer 100 8552447077")
        return
    
    # بررسی اینکه به خودش نده
    if target_id == user_id:
        await update.message.reply_text("❌ نمیتونی به خودت سکه بدی!")
        return
    
    # بررسی وجود کاربر گیرنده
    if target_id not in user_data:
        await update.message.reply_text("❌ کاربر مورد نظر وجود نداره! (حداقل یک بار ربات رو شروع کرده باشه)")
        return
    
    # بررسی موجودی فرستنده
    if amount <= 0:
        await update.message.reply_text("❌ مبلغ باید بیشتر از صفر باشه!")
        return
    
    if amount > get_balance(user_id):
        await update.message.reply_text(f"❌ سکه کافی نداری! موجودی: {get_balance(user_id)}")
        return
    
    # انجام انتقال
    change_balance(user_id, -amount)
    change_balance(target_id, amount)
    
    await update.message.reply_text(f"✅ {amount} سکه به کاربر {target_id} منتقل شد!\n💰 موجودی جدید تو: {get_balance(user_id)}")
    
    # اطلاع به گیرنده (اگه ربات بهش پیام بده)
    try:
        await context.bot.send_message(chat_id=target_id, text=f"🎁 کاربر {user_id} بهت {amount} سکه هدیه داد!\n💰 موجودی جدیدت: {get_balance(target_id)}")
    except:
        pass  # اگه کاربر ربات رو بلاک کرده باشه

# ======== دستورات ادمین (فقط خودت) ========
async def add_coin(update, context):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ فقط ادمین!")
        return
    try:
        amount = int(context.args[0])
        user_id = update.effective_user.id
        change_balance(user_id, amount)
        await update.message.reply_text(f"✅ {amount} سکه اضافه شد. موجودی: {get_balance(user_id)}")
    except:
        await update.message.reply_text("❌ دستور: /addcoin 500")

async def set_coin(update, context):
    if update.effective_user.id != ADMIN_ID:
        await update.message.reply_text("❌ فقط ادمین!")
        return
    try:
        amount = int(context.args[0])
        user_id = update.effective_user.id
        get_user(user_id)['balance'] = amount
        await update.message.reply_text(f"✅ موجودی تنظیم شد: {amount}")
    except:
        await update.message.reply_text("❌ دستور: /setcoin 50000")

# ======== دکمه‌های ناشناخته ========
async def unknown(update, context):
    await update.callback_query.answer("❌ نامعتبر!", show_alert=True)

# ======== اصلی ========
def main():
    if TOKEN == "توکن_ربات_خود_را_اینجا_بذار":
        print("⚠️ لطفاً توکن ربات را در کد قرار دهید!")
        return

    app = Application.builder().token(TOKEN).build()

    # دستورات عمومی
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_cmd))

    # دستور انتقال
    app.add_handler(CommandHandler("transfer", transfer_coin))

    # دستورات ادمین
    app.add_handler(CommandHandler("addcoin", add_coin))
    app.add_handler(CommandHandler("setcoin", set_coin))

    # دکمه‌ها
    app.add_handler(CallbackQueryHandler(dice_game, pattern='^dice$'))
    app.add_handler(CallbackQueryHandler(bet_menu, pattern='^bet$'))
    app.add_handler(CallbackQueryHandler(bet_choice, pattern='^bet_even|bet_odd$'))
    app.add_handler(CallbackQueryHandler(guess_menu, pattern='^guess$'))
    app.add_handler(CallbackQueryHandler(show_balance, pattern='^balance$'))
    app.add_handler(CallbackQueryHandler(help_cmd, pattern='^help$'))
    app.add_handler(CallbackQueryHandler(back, pattern='^back$'))
    app.add_handler(CallbackQueryHandler(unknown))

    # پیام‌های متنی
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_bet))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_guess))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_guess_number))

    print("✅ ربات روشن شد!")
    print("🎮 دستورات:")
    print("  /addcoin 500  - اضافه کردن سکه به خودت (فقط ادمین)")
    print("  /setcoin 50000 - تنظیم موجودی (فقط ادمین)")
    print("  /transfer 100 8552447077 - انتقال سکه به کاربر دیگر")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
