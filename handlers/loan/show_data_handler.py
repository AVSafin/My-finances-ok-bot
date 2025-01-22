from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, ConversationHandler
from data_storage import load_data, save_data
from keyboards.keyboards import main_keyboard, show_keyboard
from handlers import CHOOSING_ACTION
from datetime import datetime
from utils.calculations import calculate_annuity_payment, calculate_payments_schedule
async def show_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отображает сохраненные данные."""
    query = update.callback_query
    chat_id = update.effective_chat.id
    keyboard = main_keyboard
    if query:
        await query.answer()
        if query.data == "start":
             await query.edit_message_text(text="Вы вернулись в главное меню.", reply_markup = main_keyboard)
             return ConversationHandler.END
        keyboard = InlineKeyboardMarkup([[InlineKeyboardButton("Главное меню", callback_data="start")]])
        loan_index = query.data.split("_")[-1]
        try:
            data = load_data()
            loan = data["loans"][int(loan_index)]
            loan_amount = loan["loan_amount"]
            interest_rate = loan["interest_rate"]
            loan_term = loan["loan_term"]
            payment_date = loan["payment_date"]
            bank_name = loan["bank_name"]
            loan_purpose = loan["loan_purpose"]

            payment = calculate_annuity_payment(float(loan_amount), float(interest_rate), int(loan_term))
            schedule = loan["schedule"]

            total_paid = 0
            for item in schedule:
                  total_paid += item["payment"]
            remaining_debt = float(loan_amount) - total_paid if float(loan_amount) > total_paid else 0

            today = datetime.now()
            upcoming_payments = []
            for item in schedule:
                  payment_datetime = datetime.strptime(item['date'], "%Y-%m-%d")
                  if payment_datetime > today:
                       upcoming_payments.append(item)
                       if len(upcoming_payments) == 2:
                           break

            message_text = (
                f"Банк: {bank_name}\n"
                f"Цель кредита: {loan_purpose}\n"
                f"Сумма кредита: {loan_amount:.2f}\n"
                f"Процентная ставка: {interest_rate:.2f}%\n"
                f"Срок кредита (месяцы): {loan_term}\n"
                f"Дата первого платежа: {payment_date}\n"
                f"Ежемесячный платеж: {payment:.2f}\n\n"
                f"Остаток долга: {remaining_debt:.2f}\n"
            )

            if upcoming_payments:
                message_text += "Ближайшие платежи:\n"
                for i, item in enumerate(upcoming_payments):
                     message_text += f"{item['date']}: {item['payment']:.2f}\n"
            else:
                 message_text += "Нет будущих платежей\n"

            message_text += "График платежей:\n"

            formatted_schedule = "```\n"
            formatted_schedule += "Дата      | Основной долг | Проценты   | Сумма   \n"
            formatted_schedule += "----------|---------------|------------|---------\n"
            for i, item in enumerate(schedule):
                if i >= 5:
                    formatted_schedule += "...\n(показаны только первые 5 месяцев)\n"
                    break
                formatted_schedule += (
                    f"{item['date']} | {item['principal']:>13.2f} | {item['interest']:>10.2f} | {item['payment']:>7.2f}\n"
                )
            formatted_schedule += "```"
            message_text += formatted_schedule

            await query.edit_message_text(text=message_text, reply_markup=keyboard, parse_mode='Markdown')
            return ConversationHandler.END
        except (KeyError, IndexError, ValueError):
              await query.edit_message_text(text="Произошла ошибка при получении данных", reply_markup = main_keyboard)
              return CHOOSING_ACTION
    elif (
        "loan_amount" in context.user_data
        and "interest_rate" in context.user_data
        and "loan_term" in context.user_data
        and "payment_date" in context.user_data
        and "bank_name" in context.user_data
        and "loan_purpose" in context.user_data
    ):
        loan_amount = context.user_data["loan_amount"]
        interest_rate = context.user_data["interest_rate"]
        loan_term = context.user_data["loan_term"]
        payment_date = context.user_data["payment_date"]
        bank_name = context.user_data["bank_name"]
        loan_purpose = context.user_data["loan_purpose"]

        payment = calculate_annuity_payment(float(loan_amount), float(interest_rate), int(loan_term))
        schedule = calculate_payments_schedule(float(loan_amount), float(interest_rate), int(loan_term), int(payment_date[8:10]))

        new_loan = {
            "loan_amount": loan_amount,
            "interest_rate": interest_rate,
            "loan_term": loan_term,
            "payment_date": payment_date,
            "schedule": schedule,
            "bank_name": bank_name,
            "loan_purpose": loan_purpose,
        }
        data = load_data()
        if "loans" not in data:
            data["loans"] = []
        data["loans"].append(new_loan)
        save_data(data)

        await context.bot.send_message(chat_id=chat_id, text="Данные сохранены.", reply_markup=main_keyboard)
        return ConversationHandler.END

    else:
         if query:
             await query.edit_message_text(text="Нет данных для отображения. Пожалуйста, введите данные через меню расчета кредита.", reply_markup = main_keyboard)
         else:
            await context.bot.send_message(
                chat_id=chat_id,
                text="Нет данных для отображения. Пожалуйста, введите данные через меню расчета кредита.",
                reply_markup = main_keyboard
            )
         return CHOOSING_ACTION
