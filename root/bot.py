import os
import logging
#from datetime import date
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

from handlers.forecast.actions import (
    calculate_daily_balance_start,
    ask_balance,
    ask_salary_day,
    cancel,
    daily_balance_handler,
    ASK_BALANCE,
    ASK_SALARY_DAY,
    daily_balance_handler,
)

from constants import MAIN_MENU, CREDITS_MENU, SAVINGS_MENU, FORECAST_MENU, CREDIT_MODIFICATION_MENU, CREDIT_REPAYMENT_MENU

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    filename="bot.log"
)

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
        await update.message.reply_text("Вы в разделе 'Прогнозирование'. Выберите действие:", reply_markup=keyboard)
        context.user_data["current_section"] = "forecast"

# Обработка кнопки "Назад"
async def handle_back_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает кнопку 'Назад'."""
    if update.message.text == "Назад":
        keyboard = get_keyboard(MAIN_MENU)
        await update.message.reply_text("Вы вернулись в главное меню.", reply_markup=keyboard)
        context.user_data["current_section"] = None

# Обработчик ошибок

async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Log the error and send a telegram message to notify the developer."""
    logger.error(msg="Исключение при обработке обновления:", exc_info=context.error)
    if update:
        try:
            await update.message.reply_text(
                "Произошла непредвиденная ошибка при обработке вашего сообщения. Пожалуйста, попробуйте позже."
            )
        except TelegramError as e:
            logger.error(f"Не удалось отправить сообщение об ошибке пользователю: {e}")



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

    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(
                filters.Regex("^Рассчитать остаток на день$"), calculate_daily_balance_start
            ),
        ],
        states={
            ASK_BALANCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_balance)],
            ASK_SALARY_DAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_salary_day)],
        },
        fallbacks=[CommandHandler("cancel", cancel)],
    )
    application.add_handler(conv_handler)
    
    # Обработчики для кнопок в разделе "Кредиты"
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^Просмотреть кредиты$"), view_credits))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^График платежей$"), payment_schedule))

    
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