from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from keyboards.keyboards import main_keyboard, purpose_keyboard
from handlers import (
    CHOOSING_ACTION,
    LOAN_PURPOSE
)
from .loan_handlers_data import top_purposes

async def get_bank_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
     query = update.callback_query
     if query.data == "back_to_main":
          await query.answer()
          await query.edit_message_text(text="Вы вернулись в главное меню.", reply_markup = main_keyboard)
          return CHOOSING_ACTION
     bank = query.data.split("_")[1]
     context.user_data["bank_name"] = bank
     await query.answer()
     await query.edit_message_text(text="Выберите цель кредита:", reply_markup=purpose_keyboard(top_purposes))
     return LOAN_PURPOSE
