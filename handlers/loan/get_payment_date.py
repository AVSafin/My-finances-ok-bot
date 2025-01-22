from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from keyboards.keyboards import main_keyboard, bank_keyboard
from handlers import (
    CHOOSING_ACTION,
    BANK_NAME,
)
from handlers.loan.loan_handlers_data import top_banks

async def get_payment_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получает дату первого платежа."""
    text = update.message.text
    if text == "Назад":
       await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Вы вернулись в главное меню",
             reply_markup = main_keyboard
       )
       return CHOOSING_ACTION
    try:
       payment_date = text
       context.user_data["payment_date"] = payment_date
       await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Выберите банк:",
            reply_markup = bank_keyboard(top_banks)
       )
       return BANK_NAME
    except ValueError:
        await context.bot.send_message(
            chat_id=update.effective_chat.id, text="Пожалуйста, введите корректную дату"
        )
        return PAYMENT_DATE