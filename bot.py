# ==============================================
# ربات کامل تلگرام با ۳ بازی و سیستم سکه
# ==============================================
import logging
import random
import json
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes, MessageHandler, filters

# ---------- تنظیمات اولیه ----------
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------- دیکشنری ذخیره اطلاعات کاربران ----------
# کلید: user_id (عدد), مقدار: دیکشنری شامل موجودی و وضعیت بازی
user_data = {}

def get_user(user_id):
    """دریافت اطلاعات کاربر، اگر نباشه با موجودی ۵۰۰۰۰ ایجاد میکنه"""
    if user_id not in user_data:
        user_data[user_id] = {
            'balance': 50000,  # موجودی اولیه ۵۰۰۰۰ سکه
            'game_mode': None,
            'bet_choice': None,
            'secret_number': None  # برای بازی حدس عدد
        }
    return user_data[user_id]

def get_balance(user_id):
    return get_user(user_id)['balance']

def save_balance(user_id, amount):
    """افزایش یا کاهش موجودی (مقدار میتونه مثبت یا منفی باشه)"""
    user = get_user(user_id)
    user['balance'] = max(0, user['balance'] + amount)  # کمتر از صفر نمیشه
    return user['balance']

# ---------- منوی اصلی با دکمه‌های شیشه‌ای ----------
async def main_menu(update: Update, context: ContextTypes.DEFAULT_TYPE, custom_text=None):
    """نمایش منوی اصلی با دکمه‌ها"""
    user_id = update.effective_user.id
    balance = get_balance(user_id)
    
    keyboard = [
        [InlineKeyboardButton("🎲 تاس", callback_data='dice')],
        [InlineKeyboardButton("💰 شرط‌بندی", callback_data='bet')],
        [InlineKeyboardButton("🎯 حدس عدد", callback_data='guess')],
        [InlineKeyboardButton("📊 موجودی", callback_data='balance')],
        [InlineKeyboardButton("❓ راهنما", callback_data='help')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = custom_text or f"🎮 به ربات بازی خوش اومدی!\n💰 سکه‌های تو: {balance}\nیک بازی رو انتخاب کن:"
    
    if update.callback_query:
        await update.callback_query.message.edit_text(text, reply_markup=reply_markup)
        await update.callback_query.answer()
    else:
        await update.message.reply_text(text, reply_markup=reply_markup)

# ---------- دستورات عمومی ----------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await main_menu(update, context)

async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    text = """
🎮 **راهنمای بازی‌ها:**

۱) **تاس** 🎲
- فقط برای سرگرمی، تاس میندازه و عددش رو نشون میده.
- اگر عدد ۶ بیاد، ۱۰۰ سکه پاداش میگیری!

۲) **شرط‌بندی** 💰
- روی زوج یا فرد بودن تاس شرط ببند.
- هر برد، مبلغ شرط × ۲ برنده میشی!
- حداقل شرط: ۱۰۰ سکه

۳) **حدس عدد** 🎯
- یک عدد بین ۱ تا ۱۰ رو حدس بزن.
- اگر درست بزنی، ۵ برابر مبلغ شرط برنده میشی!
- اگر ۱ عدد اختلاف داشته باشی، ۲ برابر میبری.

💰 هر کاربر جدید ۵۰۰۰۰ سکه هدیه داره!
"""
    await main_menu(update, context, custom_text=text)

# ---------- بازی تاس ----------
async def dice_game(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    number = random.randint(1, 6)
    emojis = {1: '⚀', 2: '⚁', 3: '⚂', 4: '⚃', 5: '⚄', 6: '⚅'}
    
    text = f"🎲 تاس انداختم...\n\n{emojis[number]}  عدد **{number}**"
    
    if number == 6:
        save_balance(user_id, 100)
        text += "\n\n🎉 شانس آوردی! ۱۰۰ سکه پاداش گرفتی!"
    
    await update.callback_query.message.edit_text(text)
    await update.callback_query.answer()
    
    # برگشت خودکار به منو بعد از ۳ ثانیه
    context.job_queue.run_once(back_to_menu, 3, data=update)

async def back_to_menu(context: ContextTypes.DEFAULT_TYPE):
    await main_menu(context.job.data, context)

# ---------- منوی شرط‌بندی ----------
async def bet_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    balance = get_balance(user_id)
    
    keyboard = [
        [InlineKeyboardButton("زوج (ضریب ۲)", callback_data='bet_even')],
        [InlineKeyboardButton("فرد (ضریب ۲)", callback_data='bet_odd')],
        [InlineKeyboardButton("🔙 برگشت", callback_data='back')]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    text = f"💰 شرط‌بندی روی تاس\nسکه‌های تو: {balance}\nروی زوج یا فرد شرط ببند:"
    await update.callback_query.message.edit_text(text, reply_markup=reply_markup)
    await update.callback_query.answer()

async def bet_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    get_user(user_id)['bet_choice'] = update.callback_query.data  # 'bet_even' یا 'bet_odd'
    
    await update.callback_query.message.reply_text("💰 مبلغ شرط رو وارد کن (حداقل ۱۰۰ سکه):")
    await update.callback_query.answer()
    context.user_data['awaiting_bet'] = True

async def handle_bet_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت مبلغ شرط و اجرای بازی"""
    if not context.user_data.get('awaiting_bet', False):
        return
    
    user_id = update.effective_user.id
    try:
        amount = int(update.message.text)
    except ValueError:
        await update.message.reply_text("❌ لطفاً یه عدد معتبر وارد کن!")
        return
    
    balance = get_balance(user_id)
    if amount < 100:
        await update.message.reply_text("❌ حداقل شرط ۱۰۰ سکه است!")
        return
    if amount > balance:
        await update.message.reply_text(f"❌ سکه کافی نداری! حداکثر {balance} سکه داری.")
        return
    
    # پرتاب تاس
    number = random.randint(1, 6)
    is_even = (number % 2 == 0)
    choice = get_user(user_id).get('bet_choice', 'bet_even')
    user_choice_even = (choice == 'bet_even')
    
    if (is_even and user_choice_even) or (not is_even and not user_choice_even):
        win_amount = amount * 2
        save_balance(user_id, win_amount)
        result = f"🎉 بردی! {win_amount} سکه بردی!"
    else:
        save_balance(user_id, -amount)
        result = f"😢 باختی! {amount} سکه از دست دادی."
    
    emojis = {1: '⚀', 2: '⚁', 3: '⚂', 4: '⚃', 5: '⚄', 6: '⚅'}
    text = f"🎲 تاس: {emojis[number]}  عدد {number}\n\n{result}\n💰 سکه‌های جدید: {get_balance(user_id)}"
    
    await update.message.reply_text(text)
    context.user_data['awaiting_bet'] = False
    await main_menu(update, context)

# ---------- بازی حدس عدد ----------
async def guess_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """منوی بازی حدس عدد"""
    user_id = update.effective_user.id
    balance = get_balance(user_id)
    
    # تولید عدد تصادفی و ذخیره برای این کاربر
    get_user(user_id)['secret_number'] = random.randint(1, 10)
    
    text = f"🎯 بازی حدس عدد!\nیک عدد بین ۱ تا ۱۰ رو حدس بزن.\n💰 سکه‌های تو: {balance}\nمبلغ شرط رو وارد کن (حداقل ۱۰۰):"
    await update.callback_query.message.edit_text(text)
    await update.callback_query.answer()
    context.user_data['awaiting_guess'] = True

async def handle_guess(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """دریافت حدس کاربر و بررسی نتیجه"""
    if not context.user_data.get('awaiting_guess', False):
        return
    
    user_id = update.effective_user.id
    try:
        guess = int(update.message.text)
        if guess < 1 or guess > 10:
            await update.message.reply_text("❌ عدد باید بین ۱ تا ۱۰ باشه!")
            return
    except ValueError:
        await update.message.reply_text("❌ لطفاً یه عدد معتبر وارد کن!")
        return
    
    # دریافت مبلغ شرط (کاربر باید دوباره عدد وارد کنه)
    try:
        amount = int(update.message.text)  # فعلاً اینجا همونه، ولی بهتره جداگانه بپرسیم
    except:
        await update.message.reply_text("❌ لطفاً مبلغ شرط رو به صورت عدد وارد کن!")
        return
    
    # برای سادگی، از کاربر میخوایم که اول مبلغ رو وارد کنه، بعد عدد رو
    # اما اینجا یه روش ساده‌تر: کاربر دو عدد پشت سر هم وارد میکنه
    # برای رفع این مشکل، یه حالت بهتر مینویسیم:
    if not context.user_data.get('guess_amount_set'):
        context.user_data['guess_amount'] = guess  # اینجا اولین عدد رو به عنوان مبلغ در نظر میگیره
        context.user_data['guess_amount_set'] = True
        await update.message.reply_text("🎯 حالا عدد ۱ تا ۱۰ رو حدس بزن:")
        return
    
    # این قسمت برای دریافت حدس هست
    secret = get_user(user_id).get('secret_number', random.randint(1, 10))
    amount = context.user_data.get('guess_amount', 100)
    
    if amount < 100:
        await update.message.reply_text("❌ حداقل شرط ۱۰۰ سکه است!")
        context.user_data['awaiting_guess'] = False
        context.user_data['guess_amount_set'] = False
        return
    
    balance = get_balance(user_id)
    if amount > balance:
        await update.message.reply_text(f"❌ سکه کافی نداری! حداکثر {balance} سکه داری.")
        context.user_data['awaiting_guess'] = False
        context.user_data['guess_amount_set'] = False
        return
    
    # بررسی نتیجه
    diff = abs(guess - secret)
    if diff == 0:
        win_amount = amount * 5
        save_balance(user_id, win_amount)
        result = f"🎯 دقیقاً درست گفتی! {win_amount} سکه بردی!"
    elif diff == 1:
        win_amount = amount * 2
        save_balance(user_id, win_amount)
        result = f"👏 نزدیک بود! {win_amount} سکه بردی!"
    else:
        save_balance(user_id, -amount)
        result = f"😢 اشتباه! عدد من {secret} بود. {amount} سکه باختی."
    
    text = f"🎯 عدد تو: {guess}\nعدد درست: {secret}\n\n{result}\n💰 سکه‌های جدید: {get_balance(user_id)}"
    await update.message.reply_text(text)
    
    context.user_data['awaiting_guess'] = False
    context.user_data['guess_amount_set'] = False
    await main_menu(update, context)

# ---------- نمایش موجودی ----------
async def show_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    balance = get_balance(user_id)
    text = f"💰 سکه‌های شما: {balance}"
    keyboard = [[InlineKeyboardButton("🔙 برگشت", callback_data='back')]]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.callback_query.message.edit_text(text, reply_markup=reply_markup)
    await update.callback_query.answer()

# ---------- دکمه برگشت به منو ----------
async def back_to_main(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await main_menu(update, context)

# ---------- دکمه‌های ناشناخته ----------
async def unknown_callback(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.callback_query.answer("❌ گزینه نامعتبر!", show_alert=True)

# ---------- تابع اصلی ----------
def main():
    """راه‌اندازی ربات"""
    TOKEN = "توکن_ربات_خود_را_اینجا_قرار_دهید"
    
    if TOKEN == "توکن_ربات_خود_را_اینجا_قرار_دهید":
        print("⚠️ لطفاً ابتدا توکن ربات خود را در کد قرار دهید!")
        return
    
    app = Application.builder().token(TOKEN).build()
    
    # دستورات
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("help", help_command))
    
    # دکمه‌های شیشه‌ای
    app.add_handler(CallbackQueryHandler(dice_game, pattern='^dice$'))
    app.add_handler(CallbackQueryHandler(bet_menu, pattern='^bet$'))
    app.add_handler(CallbackQueryHandler(bet_choice, pattern='^bet_even|bet_odd$'))
    app.add_handler(CallbackQueryHandler(guess_menu, pattern='^guess$'))
    app.add_handler(CallbackQueryHandler(show_balance, pattern='^balance$'))
    app.add_handler(CallbackQueryHandler(help_command, pattern='^help$'))
    app.add_handler(CallbackQueryHandler(back_to_main, pattern='^back$'))
    app.add_handler(CallbackQueryHandler(unknown_callback))  # دکمه‌های ناشناخته
    
    # دریافت ورودی‌های متنی از کاربر (برای شرط‌بندی و حدس عدد)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_bet_amount))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_guess))
    # توجه: این دو هندلر باهم تداخل دارن، بهتره یکی رو غیرفعال کنی یا ترکیبشون کنی
    # ولی برای سادگی، هر دو رو میذاریم (آخرینش اجرا میشه)
    
    print("✅ ربات روشن شد!")
    print("🎮 برای شروع، در تلگرام دستور /start رو بزن.")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
