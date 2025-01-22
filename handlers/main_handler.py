from telegram import Update
from telegram.ext import ContextTypes
import logging
from keyboards.keyboards import credits_menu_keyboard, main_keyboard, show_keyboard, loan_keyboard
from handlers.loan.get_loan_amount import get_loan_amount
from handlers.loan.get_interest_rate import get_interest_rate
from handlers.loan.get_loan_term import get_loan_term
from handlers.loan.get_payment_date import get_payment_date
from handlers.loan.get_bank_name import get_bank_name
from handlers.loan.get_loan_purpose import get_loan_purpose
from handlers.loan.show_data_handler import show_data
from handlers.loan.delete_loan_handler import delete_loan


# Choose action depending on user message
async def choose_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_text = update.message.text
    logging.info(f"Получено сообщение от пользователя {update.message.from_user.username}: {user_text}")

    if user_text == "Кредиты":
        reply_markup = credits_menu_keyboard
        await update.message.reply_text("Выбери действие с кредитом:", reply_markup=reply_markup)
    elif user_text == "Сбережения":
        await update.message.reply_text("Раздел в разработке")
    elif user_text == "Прогнозирование":
        await update.message.reply_text("Раздел в разработке")
    elif user_text == "Добавить кредит":
        await get_loan_amount(update, context)
    elif user_text == "Просмотреть кредиты":
        await show_data(update, context)
    elif user_text == "Удалить кредит":
        await delete_loan(update, context)
    elif user_text == "Назад":
        await update.message.reply_text("Вы в главном меню", reply_markup=main_keyboard)
    else:
        await update.message.reply_text("Неизвестная команда")