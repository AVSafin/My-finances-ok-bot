import os
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
)

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

def main():
    """Запускает бота."""
    token = os.getenv("BOT_TOKEN")
    if not token:
        raise ValueError("Токен бота не найден! Добавьте его в Secrets как 'BOT_TOKEN'.")

    application = Application.builder().token(token).build()

    # Обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^Кредиты$"), handle_menu_selection))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^Сбережения$"), handle_menu_selection))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^Прогнозирование$"), handle_menu_selection))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^Назад$"), handle_back_button))

    # ConversationHandler для добавления кредита
    add_credit_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & filters.Regex("^Добавить кредит$"), start_add_credit)],
        states={
            0: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_bank)],
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_category)],
            2: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_amount)],
            3: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_rate)],
            4: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_term)],
            5: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_day)],
            6: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_date)],
        },
        fallbacks=[],
    )
    application.add_handler(add_credit_handler)

    application.run_polling()

if __name__ == "__main__":
    main()