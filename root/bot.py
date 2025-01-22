import os
import logging
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    filters,
    ContextTypes,
    ConversationHandler,
)
from handlers.credits.actions import (
    start_add_credit,
    ask_bank,
    ask_category,
    ask_amount,
    ask_rate,
    ask_term,
    ask_day,
    ask_date,
    ASK_BANK,
    ASK_CATEGORY,
    ASK_AMOUNT,
    ASK_RATE,
    ASK_TERM,
    ASK_DAY,
    ASK_DATE,
    view_credits,
    payment_schedule,
    delete_credit,
    confirm_delete_credit,
)

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Главные клавиатуры
MAIN_MENU = [["Кредиты"], ["Сбережения"], ["Прогнозирование"]]
CREDITS_MENU = [["Добавить кредит", "Просмотреть кредиты"], ["График платежей", "Удалить кредит"], ["Назад"]]
SAVINGS_MENU = [["Назад"]]
FORECAST_MENU = [["Назад"]]

def get_keyboard(buttons):
    """Утилита для создания клавиатуры."""
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отображает главное меню."""
    keyboard = get_keyboard(MAIN_MENU)
    await update.message.reply_text("Добро пожаловать! Выберите раздел:", reply_markup=keyboard)
    context.user_data["current_section"] = None

# Обработка главного меню
async def handle_menu_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает выбор из главного меню."""
    text = update.message.text

    if text == "Кредиты":
        keyboard = get_keyboard(CREDITS_MENU)
        await update.message.reply_text("Вы в разделе 'Кредиты'. Выберите действие:", reply_markup=keyboard)
        context.user_data["current_section"] = "credits"
    elif text == "Сбережения":
        keyboard = get_keyboard(SAVINGS_MENU)
        await update.message.reply_text("Вы в разделе 'Сбережения'.", reply_markup=keyboard)
        context.user_data["current_section"] = "savings"
    elif text == "Прогнозирование":
        keyboard = get_keyboard(FORECAST_MENU)
        await update.message.reply_text("Вы в разделе 'Прогнозирование'.", reply_markup=keyboard)
        context.user_data["current_section"] = "forecast"

# Обработка кнопки "Назад"
async def handle_back_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает кнопку 'Назад'."""
    if update.message.text == "Назад":
        keyboard = get_keyboard(MAIN_MENU)
        await update.message.reply_text("Вы вернулись в главное меню.", reply_markup=keyboard)
        context.user_data["current_section"] = None

# Обработчик ошибок
async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Логирует ошибки и отправляет сообщение разработчику."""
    logger.error(msg="Исключение при обработке обновления:", exc_info=context.error)
    # Отправка сообщения разработчику или в лог
    # await context.bot.send_message(chat_id=DEVELOPER_CHAT_ID, text=f"Произошла ошибка: {context.error}")

def main():
    """Запускает бота."""
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("Токен бота не найден! Добавьте его в переменные окружения как 'BOT_TOKEN'.")

    application = Application.builder().token(token).build()

    # Обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^Кредиты$"), handle_menu_selection))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^Сбережения$"), handle_menu_selection))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^Прогнозирование$"), handle_menu_selection))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^Назад$"), handle_back_button))

    # Обработчики для кнопок в разделе "Кредиты"
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^Просмотреть кредиты$"), view_credits))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^График платежей$"), payment_schedule))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^Удалить кредит$"), delete_credit))

    # ConversationHandler для добавления кредита
    add_credit_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & filters.Regex("^Добавить кредит$"), start_add_credit)],
        states={
            ASK_BANK: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_bank)],
            ASK_CATEGORY: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_category)],
            ASK_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_amount)],
            ASK_RATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_rate)],
            ASK_TERM: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_term)],
            ASK_DAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_day)],
            ASK_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_date)],
        },
        fallbacks=[],
    )
    application.add_handler(add_credit_handler)

    # Обработчик удаления кредита
    delete_credit_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & filters.Regex("^Удалить кредит$"), delete_credit)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_delete_credit)],
        },
        fallbacks=[],
    )
    application.add_handler(delete_credit_handler)
    
    # Регистрация обработчика ошибок
    application.add_error_handler(error_handler)

    application.run_polling()

if __name__ == "__main__":
    main()