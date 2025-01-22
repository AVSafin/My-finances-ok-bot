from telegram import Update
from telegram.ext import ContextTypes
from root.data_storage import load_data, save_data
from utils.calculations import calculate_payments_schedule

async def set_opening_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите дату открытия кредита (в формате ГГГГ-ММ-ДД):")
    return "WAITING_FOR_DATE"

async def set_payment_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Введите день платежа (число от 1 до 28):")
    return "WAITING_FOR_PAYMENT_DAY"

async def delete_loan(update: Update, context: ContextTypes.DEFAULT_TYPE):
    loan_id = context.user_data.get("loan_id")
    data = load_data()
    if loan_id and loan_id in data["loans"]:
        del data["loans"][loan_id]
        save_data(data)
        await update.message.reply_text(f"Кредит {loan_id} успешно удален.")
    else:
        await update.message.reply_text("Кредит с указанным ID не найден.")

async def update_payment_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    loan_id = context.user_data.get("loan_id")
    new_payment_day = context.user_data.get("new_payment_day")
    data = load_data()
    if loan_id and loan_id in data["loans"]:
        data["loans"][loan_id]["payment_day"] = new_payment_day
        save_data(data)
        await update.message.reply_text(f"День платежа для кредита {loan_id} изменен на {new_payment_day}.")
    else:
        await update.message.reply_text("Кредит с указанным ID не найден.")