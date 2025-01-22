from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from data_storage import load_data, save_data
from keyboards.keyboards import main_keyboard
from handlers import CHOOSING_ACTION

async def delete_loan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удаляет кредит."""
    query = update.callback_query
    await query.answer()
    loan_index = query.data.split("_")[-1]
    try:
        data = load_data()
        if "loans" in data and data["loans"]:  # Проверка на существование и непустоту списка
            del data["loans"][int(loan_index)]
            save_data(data)
            await query.edit_message_text(text="Кредит успешно удален!", reply_markup=main_keyboard)
        else:
            await query.edit_message_text(text="Список кредитов пуст.", reply_markup=main_keyboard)
    except (KeyError, IndexError, ValueError):
        await query.edit_message_text(text="Произошла ошибка при удалении кредита.", reply_markup=main_keyboard)
    return CHOOSING_ACTION