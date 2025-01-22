from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from keyboards.keyboards import main_keyboard, loan_keyboard
from handlers import (
    CHOOSING_ACTION,
     PAYMENT_DATE,
)
async def get_loan_term(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получает срок кредита в месяцах."""
    text = update.message.text
    if text == "Назад":
       await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Вы вернулись в главное меню",
             reply_markup = main_keyboard
       )
       return CHOOSING_ACTION
    try:
        loan_term = int(text)
        context.user_data["loan_term"] = loan_term
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text="Введите дату первого платежа (ГГГГ-ММ-ДД):", reply_markup = loan_keyboard
        )
        return PAYMENT_DATE
    except ValueError:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text="Пожалуйста, введите корректный срок кредита"
        )
        return LOAN_TERM