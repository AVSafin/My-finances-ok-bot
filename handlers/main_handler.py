from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler
from keyboards.keyboards import main_menu_keyboard, credits_menu_keyboard
from data_storage import load_data
from telegram import InlineKeyboardButton, InlineKeyboardMarkup
from handlers import (
    LOAN_AMOUNT,
    SHOW_DATA,
    DELETE_LOAN
)
async def choose_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
   query = update.callback_query
   if query:
    await query.answer()
    if query.data == "calculate_loan":
        await context.bot.send_message(
            chat_id=update.effective_chat.id,
            text="Введите сумму кредита:",
            reply_markup=loan_keyboard
        )
        return LOAN_AMOUNT
    elif query.data == "show_loans":
         data = load_data()
         if "loans" in data and data["loans"]:
            keyboard = []
            for index, loan in enumerate(data["loans"]):
               keyboard.append([InlineKeyboardButton(text = f"Кредит {index + 1}", callback_data=f"show_loan_{index}")])
            keyboard.append([InlineKeyboardButton("Главное меню", callback_data="start")])
            await query.edit_message_text(text="Выберите кредит для просмотра:", reply_markup=InlineKeyboardMarkup(keyboard))
         else:
             await query.edit_message_text(text="Нет сохраненных кредитов.", reply_markup=main_keyboard)
         return SHOW_DATA
    elif query.data == "delete_loans":
         data = load_data()
         if "loans" in data and data["loans"]:
            keyboard = []
            for index, loan in enumerate(data["loans"]):
                keyboard.append([InlineKeyboardButton(text = f"Кредит {index + 1}", callback_data=f"delete_loan_{index}")])
            keyboard.append([InlineKeyboardButton("Главное меню", callback_data="start")])
            await query.edit_message_text(text="Выберите кредит для удаления:", reply_markup=InlineKeyboardMarkup(keyboard))
         else:
            await query.edit_message_text(text="Нет сохраненных кредитов.", reply_markup=main_keyboard)
         return DELETE_LOAN
   else:
        await context.bot.send_message(
          chat_id=update.effective_chat.id,
          text="Выберите действие:",
          reply_markup = main_keyboard
       )
        return CHOOSING_ACTION