
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext

from handlers import main_handler
from keyboards import main_menu_keyboard

# Command to start the bot and show the main menu
async def start(update: Update, context: CallbackContext) -> None:
    reply_markup = ReplyKeyboardMarkup(main_menu_keyboard, resize_keyboard=True)
    await update.message.reply_text("Добро пожаловать! Выберите один из разделов:", reply_markup=reply_markup)

# Entry point for the bot
def main() -> None:
    application = Application.builder().token("YOUR_TELEGRAM_BOT_TOKEN").build()

    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, main_handler.handle_main_menu))

    # Run the bot
    application.run_polling()

if __name__ == "__main__":
    main()
