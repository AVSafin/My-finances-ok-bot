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
    modify_credit,
    handle_credit_choice,
    handle_action_choice,
    handle_new_payment_day,
    handle_change_date,
    handle_repayment_amount,
    handle_confirm_changes,
    CHOOSE_CREDIT,
    CHOOSE_ACTION,
    ASK_NEW_PAYMENT_DAY,
    ASK_CHANGE_DATE,
    ASK_REPAYMENT_AMOUNT,
    CONFIRM_CHANGES,
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
    start_add_expense,
    add_expense_name,
    add_expense_amount,
    add_expense_day,
    view_regular_expenses,
    get_summary,
    ADD_EXPENSE_NAME,
    ADD_EXPENSE_AMOUNT,
    ADD_EXPENSE_DAY,
    manage_income_start,
    handle_income_menu,
    add_main_income,
    add_main_income_day,
    add_advance,
    add_advance_day,
    add_extra_income,
    INCOME_MENU,
    ADD_MAIN_INCOME,
    ADD_MAIN_INCOME_DAY,
    ADD_ADVANCE,
    ADD_ADVANCE_DAY,
    ADD_EXTRA_INCOME,
)
from constants import MAIN_MENU, CREDITS_MENU, SAVINGS_MENU, FORECAST_MENU

# Настройка логирования
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
    filename="bot.log"
)

def get_keyboard(buttons):
    """Утилита для создания клавиатуры для Telegram."""
    return ReplyKeyboardMarkup(buttons, resize_keyboard=True)

# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отображает главное меню пользователю при запуске бота."""
    keyboard = get_keyboard(MAIN_MENU)
    await update.message.reply_text("Добро пожаловать! Выберите раздел:", reply_markup=keyboard)
    context.user_data["current_section"] = None

async def handle_menu_selection(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает выбор пользователем раздела из главного меню."""
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

async def handle_back_button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает нажатие кнопки 'Назад'."""
    if update.message.text == "Назад":
        keyboard = get_keyboard(MAIN_MENU)
        await update.message.reply_text("Вы вернулись в главное меню.", reply_markup=keyboard)
        context.user_data["current_section"] = None

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отменяет текущее действие и возвращает в главное меню."""
    keyboard = get_keyboard(MAIN_MENU)
    await update.message.reply_text("Действие отменено. Возврат в главное меню.", reply_markup=keyboard)
    return ConversationHandler.END

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Логирует ошибки и уведомляет пользователя о возникновении ошибки."""
    logging.error(msg="Исключение при обработке обновления:", exc_info=context.error)
    if update and update.effective_message:
        try:
            keyboard = ReplyKeyboardMarkup([["Назад"]], resize_keyboard=True)
            await update.effective_message.reply_text(
                "Произошла ошибка при обработке вашего запроса. Попробуйте вернуться в главное меню.",
                reply_markup=keyboard
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

    token = os.getenv("BOT_TOKEN")
    application = Application.builder().token(token).build()

    # Базовые обработчики
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^Кредиты$"), handle_menu_selection))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^Сбережения$"), handle_menu_selection))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^Прогнозирование$"), handle_menu_selection))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^Назад$"), handle_back_button))

    # Обработчики кредитного раздела
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^Просмотреть кредиты$"), view_credits))
    application.add_handler(MessageHandler(filters.TEXT & filters.Regex("^График платежей$"), payment_schedule))

    # Обработчик для расчета остатка
    application.add_handler(daily_balance_handler())
    application.add_handler(MessageHandler(
        filters.TEXT & filters.Regex("^Просмотреть регулярные расходы$"),
        view_regular_expenses
    ))
    application.add_handler(MessageHandler(
        filters.TEXT & filters.Regex("^Свод$"),
        get_summary
    ))
    
    # Обработчик управления доходами
    income_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^Управление доходами$"), manage_income_start)],
        states={
            INCOME_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_income_menu)],
            ADD_MAIN_INCOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_main_income)],
            ADD_MAIN_INCOME_DAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_main_income_day)],
            ADD_ADVANCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_advance)],
            ADD_ADVANCE_DAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_advance_day)],
            ADD_EXTRA_INCOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_extra_income)],
        },
        fallbacks=[MessageHandler(filters.Regex("^Отмена$"), cancel)]
    )
    application.add_handler(income_handler)

    # Обработчик добавления регулярных расходов
    regular_expenses_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^Добавить регулярный расход$"), start_add_expense)],
        states={
            ADD_EXPENSE_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_expense_name)],
            ADD_EXPENSE_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_expense_amount)],
            ADD_EXPENSE_DAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_expense_day)],
        },
        fallbacks=[MessageHandler(filters.Regex("^Отмена$"), cancel)],
    )
    application.add_handler(regular_expenses_handler)

    # Обработчик управления доходами
    income_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.Regex("^Управление доходами$"), manage_income_start)],
        states={
            INCOME_MENU: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_income_menu)],
            ADD_MAIN_INCOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_main_income)],
            ADD_MAIN_INCOME_DAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_main_income_day)],
            ADD_ADVANCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_advance)],
            ADD_ADVANCE_DAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_advance_day)],
            ADD_EXTRA_INCOME: [MessageHandler(filters.TEXT & ~filters.COMMAND, add_extra_income)],
        },
        fallbacks=[MessageHandler(filters.Regex("^Назад$"), cancel)],
    )
    application.add_handler(income_handler)

    # Обработчик добавления кредита
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
        fallbacks=[MessageHandler(filters.TEXT & filters.Regex("^Назад$"), handle_back_button)],
    )
    application.add_handler(add_credit_handler)

    # Обработчик удаления кредита
    delete_credit_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & filters.Regex("^Удалить кредит$"), delete_credit)],
        states={
            1: [MessageHandler(filters.TEXT & ~filters.COMMAND, confirm_delete_credit)],
        },
        fallbacks=[MessageHandler(filters.TEXT & filters.Regex("^Назад$"), handle_back_button)],
    )
    application.add_handler(delete_credit_handler)

    # Обработчик изменения кредита
    modify_credit_handler = ConversationHandler(
        entry_points=[MessageHandler(filters.TEXT & filters.Regex("^Изменение кредита$"), modify_credit)],
        states={
            CHOOSE_CREDIT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_credit_choice)],
            CHOOSE_ACTION: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_action_choice)],
            ASK_NEW_PAYMENT_DAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_new_payment_day)],
            ASK_CHANGE_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_change_date)],
            ASK_REPAYMENT_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_repayment_amount)],
            CONFIRM_CHANGES: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_confirm_changes)],
            ASK_NEW_PAYMENT_AMOUNT: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_new_payment_amount)],
            ASK_NEW_PAYMENT_DATE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_new_payment_date)],
        },
        fallbacks=[MessageHandler(filters.TEXT & filters.Regex("^Назад$"), handle_back_button)],
    )
    application.add_handler(modify_credit_handler)

    # Регистрация обработчика ошибок
    application.add_error_handler(error_handler)

    application.run_polling()

if __name__ == "__main__":
    main()