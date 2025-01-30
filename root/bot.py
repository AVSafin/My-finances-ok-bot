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
    view_credits,
    delete_credit,
    payment_schedule,
    ASK_BANK,
    ask_bank,
    ASK_CATEGORY,
    ask_category,
    ASK_AMOUNT,
    ask_amount,
    ASK_RATE,
    ask_rate,
    ASK_TERM,
    ask_term,
    ASK_DAY,
    ask_day,
    ASK_DATE,
    ask_date,
    confirm_delete_credit,
)
from handlers.forecast.actions import (
    calculate_daily_balance_start,
    ask_balance,
    ask_salary_day,
    daily_balance_handler,
)
from constants import MAIN_MENU, CREDITS_MENU, SAVINGS_MENU, FORECAST_MENU

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    filename="bot.log"t.log"   # Запись логов в файл
)

def get_keyboard(buttons):
    """Утилита для создания клавиатуры для Telegram."""
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отображает главное меню пользователю при запуске бота."""
    keyboard = get_keyboard(MAIN_MENU)  # Формируем клавиатуру
    await update.message.reply_text("Добро пожаловать! Выберите раздел:", reply_markup=keyboard)
    context.user_data["current_section"] = None  # Очищаем текущую секцию пользователя

async def handle_menu_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает выбор пользователем раздела из главного меню."""
    text = update.message.text
    if text == "Кредиты":
        keyboard = get_keyboard(CREDITS_MENU)
        await update.message.reply_text("Вы в разделе 'Кредиты'. Выберите действие:", reply_markup=keyboard)
        context.user_data["current_section"] = "credits"  # Запоминаем раздел для контекста
    elif text == "Сбережения":
        keyboard = get_keyboard(SAVINGS_MENU)
        await update.message.reply_text("Вы в разделе 'Сбережения'.", reply_markup=keyboard)
        context.user_data["current_section"] = "savings"
    elif text == "Прогнозирование":
        keyboard = get_keyboard(FORECAST_MENU)
        await update.message.reply_text("Вы в разделе 'Прогнозирование'. Выберите действие:", reply_markup=keyboard)
        context.user_data["current_section"] = "forecast"

# Обработка кнопки "Назад"
async def handle_back_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает нажатие кнопки 'Назад'."""
    if update.message.text == "Назад":
        keyboard = get_keyboard(MAIN_MENU)  # Возвращаемся к главному меню
        await update.message.reply_text("Вы вернулись в главное меню.", reply_markup=keyboard)
        context.user_data["current_section"] = None  # Очищаем текущую секцию тоже

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Логирует ошибки и уведомляет пользователя о возникновении ошибки."""
    logging.error(msg="Исключение при обработке обновления:", exc_info=context.error)
    if update:
        try:
            await update.message.reply_text(
                "Произошла непредвиденная ошибка при обработке вашего сообщения. Пожалуйста, попробуйте позже."
            )
        except Exception as e:
            logging.error(f"Не удалось отправить сообщение об ошибке пользователю: {e}")

def main():
    """Запускает бота."""
    import signal
    import sys
    
    logging.info("Starting bot...")

    def signal_handler(signum, frame):
        print("Получен сигнал завершения, выполняется корректное завершение...")
        sys.exit(0)

    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)

    token = os.getenv("BOT_TOKEN")  # Получаем токен из переменных окружения
    application = Application.builder().token(token).build()  # Создаем экземпляр приложения

    # Обработчики для команд и выборов меню
    application.add_handler(CommandHandler("start", start))  # Команда /start
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^Кредиты$"), handle_menu_selection))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^Сбережения$"), handle_menu_selection))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^Прогнозирование$"), handle_menu_selection))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^Назад$"), handle_back_button))

    # Обработчики для кнопок в разделе "Кредиты"
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^Просмотреть кредиты$"), view_credits))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^График платежей$"), payment_schedule))

    application.add_handler(daily_balance_handler())  # Добавляем обработчик для расчета остатка

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
        fallbacks=[],  # Указываем фоллбэки если не получается обработать ввод
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

    application.run_polling()  # Запускаем бота в режиме опроса

if __name__ == "__main__":
    main()  # Запускаем основную функцию