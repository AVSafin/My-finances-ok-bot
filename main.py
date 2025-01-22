import logging
import os
import subprocess

#настройка логирования
logging.basicConfig(
    filename='logs.txt',
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

#Пример записи лога
logging.info("Бот запущен.", extra={})


def update_git():
    try:
        # Добавить все изменения
        subprocess.run(["git", "add", "."], check=True)
        # Создать коммит
        subprocess.run(["git", "commit", "-m", "Auto-update from Replit"], check=True)
        # Отправить изменения в GitHub
        subprocess.run(["git", "push", "origin", "main"], check=True)
        print("Файлы успешно обновлены на GitHub.")
    except subprocess.CalledProcessError as e:
        print(f"Ошибка при обновлении файлов на GitHub: {e}")

update_git()

from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, CallbackContext,  PicklePersistence
from handlers import main_handler, error_handler
from keyboards.keyboards import main_keyboard, main_menu_keyboard
from dotenv import load_dotenv
load_dotenv()

# Command to start the bot and show the main menu
async def start(update: Update, context: CallbackContext) -> None:
    reply_markup = ReplyKeyboardMarkup(main_menu_keyboard, resize_keyboard=True)
    await update.message.reply_text("Добро пожаловать! Выберите один из разделов:", reply_markup=reply_markup)

# Entry point for the bot
def main() -> None:
    #persistence
    persistence = PicklePersistence(filepath="bot_data")
    application = Application.builder().token(os.getenv("TELEGRAM_BOT_TOKEN")).persistence(persistence).build()


    # Add handlers
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, main_handler.choose_action))
    application.add_error_handler(error_handler.handle_error)

    # Run the bot
    application.run_polling()

if __name__ == "__main__":
    main()
