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

OWNER_ID = 123456789012345678      # آیدی عددی خودت
ADMIN_IDS = [987654321098765432]   # آیدی مدیران (لیست)

# ========== توابع دیتا ==========
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
        result = f"🎉 بردی! +{win} سکه (۲ برابر)"
    elif user_roll < bot_roll:
        add_balance(ctx.author.id, -bet)
        result = f"😢 باختی! -{bet} سکه"
    else:
        result = "🤝 مساوی! شرط برگشت"
        # در مساوی چیزی کم نمیشه

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
        result = f"🌟 +{win} سکه (۳ برابر)"
    else:
        add_balance(ctx.author.id, -bet)
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
    user_guess = random.randint(0, 10)  # حدس کاربر (در نسخه واقعی می‌تونی ورودی بگیری)
    diff = abs(pins_down - user_guess)
    reward = max(0, bet * (10 - diff) // 10)  # پاداش متناسب با دقت

    add_balance(ctx.author.id, reward - bet)  # اگر reward > bet باشه سود می‌کنه

    embed = discord.Embed(title="🎳 بولینگ (شرطی)", color=0x00bfff)
    embed.add_field(name="پین‌های خوابیده", value=f"{pins_down} / ۱۰", inline=True)
    embed.add_field(name="حدس تو", value=f"{user_guess}", inline=True)
    embed.add_field(name="شرط", value=f"{bet} 🪙", inline=True)
    embed.add_field(name="پاداش نهایی", value=f"{reward} سکه", inline=False)
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

# ========== اجرا ==========
bot.run("توکن_ربات_خودت_اینجا")
