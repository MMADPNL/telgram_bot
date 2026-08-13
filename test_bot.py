import os
from telegram.ext import Application, CommandHandler

TOKEN = os.getenv("BOT_TOKEN")

async def start(update, context):
    await update.message.reply_text("ربات روشنه ✅")

app = Application.builder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))

print("BOT STARTED")
app.run_polling()
