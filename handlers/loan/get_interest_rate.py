from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from keyboards.keyboards import main_keyboard, loan_keyboard
from handlers import (
    CHOOSING_ACTION,
    LOAN_TERM,
)
async def get_interest_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получает годовую процентную ставку."""
    text = update.message.text
    if text == "Назад":
       await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Вы вернулись в главное меню",
             reply_markup = main_keyboard
       )
       return CHOOSING_ACTION
    try:
        interest_rate = float(text)
        context.user_data["interest_rate"] = interest_rate
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text="Введите срок кредита (в месяцах):", reply_markup = loan_keyboard
        )
        return LOAN_TERM
    except ValueError:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text="Пожалуйста, введите корректную процентную ставку"
        )
        return INTEREST_RATE