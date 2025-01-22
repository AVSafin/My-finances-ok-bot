from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from keyboards.keyboards import main_keyboard, loan_keyboard
from handlers import (
    CHOOSING_ACTION,
    INTEREST_RATE,
)
async def get_loan_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получает сумму кредита."""
    text = update.message.text
    if text == "Назад":
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Вы вернулись в главное меню",
             reply_markup = main_keyboard
        )
        return CHOOSING_ACTION
    try:
        loan_amount = float(text)
        context.user_data["loan_amount"] = loan_amount
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text="Введите годовую процентную ставку:", reply_markup = loan_keyboard
        )
        return  INTEREST_RATE
    except ValueError:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text="Пожалуйста, введите корректную сумму кредита"
        )
        return LOAN_AMOUNT