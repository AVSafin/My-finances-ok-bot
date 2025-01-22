
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import CallbackContext

from keyboards import credits_menu_keyboard
from loan_handlers_data import update_payment_date

async def handle_credits_menu(update: Update, context: CallbackContext) -> None:
    text = update.message.text
    if text == "Изменить дату платежа":
        await update.message.reply_text("Введите ID кредита, для которого нужно изменить дату платежа:")
        context.user_data['next_action'] = 'awaiting_loan_id'
    elif context.user_data.get('next_action') == 'awaiting_loan_id':
        loan_id = text.strip()
        context.user_data['loan_id'] = loan_id
        await update.message.reply_text(f"Введите новую дату платежа для кредита ID {loan_id} (в формате ГГГГ-ММ-ДД):")
        context.user_data['next_action'] = 'awaiting_new_date'
    elif context.user_data.get('next_action') == 'awaiting_new_date':
        new_date = text.strip()
        try:
            datetime.strptime(new_date, "%Y-%m-%d")
            loans = context.bot_data.get("loans", {})
            loan_id = context.user_data.get('loan_id')
            success, message = update_payment_date(loans, loan_id, new_date)
            if success:
                context.bot_data["loans"] = loans  # Save the updated loans data.
            await update.message.reply_text(message)
        except ValueError:
            await update.message.reply_text("Некорректный формат даты. Попробуйте снова (формат: ГГГГ-ММ-ДД).")
        context.user_data.pop('next_action', None)
        context.user_data.pop('loan_id', None)
    else:
        await update.message.reply_text("Пожалуйста, выберите действие из меню.", 
                                         reply_markup=ReplyKeyboardMarkup(credits_menu_keyboard, resize_keyboard=True))
