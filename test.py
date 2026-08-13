from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = "8981045477:AAHCiu01fynQ0mkwCTS_W4wlnIZfawdlzLM"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("✅ ربات روشنه! سلام داداش!")

def main():
    app = Application.builder().token(TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    print("🤖 ربات روشن شد...")
    app.run_polling()

if __name__ == "__main__":
    main()
