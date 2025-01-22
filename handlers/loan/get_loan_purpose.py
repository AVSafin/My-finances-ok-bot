from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler
from keyboards.keyboards import main_keyboard, purpose_keyboard
from handlers import (
    CHOOSING_ACTION,
)
async def get_loan_purpose(update: Update, context: ContextTypes.DEFAULT_TYPE):
     query = update.callback_query
     if query.data == "back_to_main":
          await query.answer()
          await query.edit_message_text(text="Вы вернулись в главное меню.", reply_markup = main_keyboard)
          return CHOOSING_ACTION
     purpose = query.data.split("_")[1]
     context.user_data["loan_purpose"] = purpose
     await query.answer()
     await query.edit_message_text(text="Данные сохранены, для просмотра введите /show", reply_markup=main_keyboard)
     return ConversationHandler.END