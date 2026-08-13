import discord
from discord.ext import commands
import json
import random
import os

# ========== تنظیمات اولیه ==========
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

DATA_FILE = "balances.json"
STATS_FILE = "stats.json"

OWNER_ID = 123456789012345678      # آیدی عددی خودت رو بذار اینجا
ADMIN_IDS = [987654321098765432]   # آیدی مدیران (لیست)

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

# ========== بازی تاس (شرطی) ==========
@bot.command(name="تاس")
async def dice(ctx, bet: int):
    if bet < 50 or bet > 5000:
        await ctx.send("❌ شرط باید بین **۵۰** تا **۵۰۰۰** سکه باشد!")
        return
    if get_balance(ctx.author.id) < bet:
        await ctx.send(f"❌ موجودی کافی نداری! (موجودی: {get_balance(ctx.author.id)} سکه)")
        return

    user_roll = random.randint(1, 6)
    bot_roll = random.randint(1, 6)

    if user_roll > bot_roll:
        win = bet * 2
        add_balance(ctx.author.id, win)
        update_stats(ctx.author.id, "wins")
        result = f"🎉 بردی! +{win} سکه"
    elif user_roll < bot_roll:
        add_balance(ctx.author.id, -bet)
        update_stats(ctx.author.id, "losses")
        result = f"😢 باختی! -{bet} سکه"
    else:
        update_stats(ctx.author.id, "draws")
        result = "🤝 مساوی! شرط برگشت"

    embed = discord.Embed(title="🎲 بازی تاس (شرطی)", color=0x00ff00)
    embed.add_field(name=f"{ctx.author.display_name}", value=f"🎲 {user_roll}", inline=True)
    embed.add_field(name="ربات", value=f"🤖 {bot_roll}", inline=True)
    embed.add_field(name="شرط", value=f"{bet} 🪙", inline=True)
    embed.add_field(name="نتیجه", value=result, inline=False)
    await ctx.send(embed=embed)

# ========== بازی بسکتبال (شرطی) ==========
@bot.command(name="بسکتبال")
async def basketball(ctx, bet: int):
    if bet < 50 or bet > 5000:
        await ctx.send("❌ شرط باید بین **۵۰** تا **۵۰۰۰** سکه باشد!")
        return
    if get_balance(ctx.author.id) < bet:
        await ctx.send(f"❌ موجودی کافی نداری! (موجودی: {get_balance(ctx.author.id)} سکه)")
        return

    user_score = random.choice(["گل کردی! 🏀✅", "گل نشد! ❌"])
    if user_score == "گل کردی! 🏀✅":
        win = bet * 3
        add_balance(ctx.author.id, win)
        update_stats(ctx.author.id, "wins")
        result = f"🌟 +{win} سکه"
    else:
        add_balance(ctx.author.id, -bet)
        update_stats(ctx.author.id, "losses")
        result = f"💔 -{bet} سکه"

    embed = discord.Embed(title="🏀 بسکتبال (شرطی)", color=0xff8c00)
    embed.add_field(name="شوت تو", value=user_score, inline=False)
    embed.add_field(name="شرط", value=f"{bet} 🪙", inline=True)
    embed.add_field(name="نتیجه", value=result, inline=False)
    await ctx.send(embed=embed)

# ========== بازی بولینگ (شرطی) ==========
@bot.command(name="بولینگ")
async def bowling(ctx, bet: int):
    if bet < 50 or bet > 5000:
        await ctx.send("❌ شرط باید بین **۵۰** تا **۵۰۰۰** سکه باشد!")
        return
    if get_balance(ctx.author.id) < bet:
        await ctx.send(f"❌ موجودی کافی نداری! (موجودی: {get_balance(ctx.author.id)} سکه)")
        return

    pins_down = random.randint(0, 10)
    user_guess = random.randint(0, 10)
    diff = abs(pins_down - user_guess)
    reward = max(0, bet * (10 - diff) // 10)

    if reward > bet:
        add_balance(ctx.author.id, reward - bet)
        update_stats(ctx.author.id, "wins")
        result = f"🎉 +{reward} سکه"
    elif reward < bet:
        add_balance(ctx.author.id, reward - bet)
        update_stats(ctx.author.id, "losses")
        result = f"😢 -{bet - reward} سکه"
    else:
        result = "🤝 دقیقاً شرط برگشت"

    embed = discord.Embed(title="🎳 بولینگ (شرطی)", color=0x00bfff)
    embed.add_field(name="پین‌های خوابیده", value=f"{pins_down} / ۱۰", inline=True)
    embed.add_field(name="حدس تو", value=f"{user_guess}", inline=True)
    embed.add_field(name="شرط", value=f"{bet} 🪙", inline=True)
    embed.add_field(name="پاداش نهایی", value=f"{reward} سکه", inline=False)
    embed.add_field(name="نتیجه", value=result, inline=False)
    await ctx.send(embed=embed)

# ========== موجودی ==========
@bot.command(name="موجودی")
async def balance(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author
    bal = get_balance(member.id)
    embed = discord.Embed(title=f"💰 موجودی {member.display_name}", color=0xffd700)
    embed.add_field(name="سکه", value=f"{bal} 🪙", inline=False)
    await ctx.send(embed=embed)

# ========== انتقال (عمومی) ==========
@bot.command(name="انتقال")
async def transfer(ctx, amount: int, member: discord.Member):
    if amount <= 0:
        await ctx.send("❌ مقدار باید مثبت باشه!")
        return
    if member.id == ctx.author.id:
        await ctx.send("❌ نمی‌تونی به خودت انتقال بدی!")
        return
    if get_balance(ctx.author.id) < amount:
        await ctx.send("❌ موجودی کافی نداری!")
        return

    add_balance(ctx.author.id, -amount)
    add_balance(member.id, amount)
    await ctx.send(f"✅ {amount} سکه به {member.mention} انتقال داده شد.")

# ========== کسر (فقط مالک و مدیران) ==========
@bot.command(name="کسر")
@commands.has_permissions(administrator=True)
async def deduct(ctx, amount: int, member: discord.Member):
    if ctx.author.id != OWNER_ID and ctx.author.id not in ADMIN_IDS:
        await ctx.send("❌ شما اجازه کسر از دیگران را ندارید!")
        return
    if amount <= 0:
        await ctx.send("❌ مقدار باید مثبت باشه!")
        return
    current = get_balance(member.id)
    if current < amount:
        await ctx.send(f"❌ موجودی {member.display_name} کمتر از {amount} است!")
        return

    add_balance(member.id, -amount)
    await ctx.send(f"✅ {amount} سکه از {member.mention} کسر شد. (توسط {ctx.author.display_name})")

# ========== ریست موجودی (همه به جز مالک) ==========
@bot.command(name="ریست")
async def reset_all(ctx):
    if ctx.author.id != OWNER_ID:
        await ctx.send("❌ فقط مالک ربات می‌تونه موجودی رو ریست کنه!")
        return

    owner_balance = get_balance(OWNER_ID)

    confirm = await ctx.send("⚠️ **آیا مطمئنی؟** موجودی همه کاربران (به جز خودت) صفر می‌شه! (بله/خیر)")
    def check(m):
        return m.author == ctx.author and m.content.lower() in ["بله", "خیر"]

    try:
        response = await bot.wait_for("message", timeout=30.0, check=check)
    except:
        await ctx.send("⏰ زمان تأخیر! عملیات لغو شد.")
        return

    if response.content.lower() == "خیر":
        await ctx.send("❌ عملیات ریست لغو شد.")
        return

    save_data({})
    set_balance(OWNER_ID, owner_balance)
    await ctx.send(f"✅ **همه موجودی‌ها به صفر رسید.** (موجودی شما: {owner_balance} سکه دست نخورده ماند) 🔄")

# ========== ریست آمار بازی‌ها (فقط مالک) ==========
@bot.command(name="ریست‌بازی")
async def reset_stats(ctx):
    if ctx.author.id != OWNER_ID:
        await ctx.send("❌ فقط مالک ربات می‌تونه آمار رو ریست کنه!")
        return

    confirm = await ctx.send("⚠️ **همه آمار بازی‌ها پاک میشه!** ادامه بدی؟ (بله/خیر)")
    def check(m):
        return m.author == ctx.author and m.content.lower() in ["بله", "خیر"]

    try:
        response = await bot.wait_for("message", timeout=30.0, check=check)
    except:
        await ctx.send("⏰ زمان تأخیر! عملیات لغو شد.")
        return

    if response.content.lower() == "خیر":
        await ctx.send("❌ عملیات ریست لغو شد.")
        return

    save_stats({})
    await ctx.send("✅ **همه آمار بازی‌ها با موفقیت صفر شد.** از نو شروع می‌کنیم! 🔄")

# ========== نمایش آمار ==========
@bot.command(name="آمار")
async def stats(ctx, member: discord.Member = None):
    if member is None:
        member = ctx.author
    stats = get_stats(member.id)
    embed = discord.Embed(title=f"📊 آمار بازی‌های {member.display_name}", color=0x9b59b6)
    embed.add_field(name="🏆 برد", value=stats["wins"], inline=True)
    embed.add_field(name="💔 باخت", value=stats["losses"], inline=True)
    embed.add_field(name="🤝 مساوی", value=stats["draws"], inline=True)
    await ctx.send(embed=embed)

# ========== اجرا ==========
bot.run("توکن_ربات_خودت_اینجا")
