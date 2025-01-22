from telegram import Update
from root.data_storage import load_data

async def show_next_payments(update: Update, context):
    data = load_data()
    payments = []
    for loan in data["loans"].values():
        payments.extend(loan["schedule"])
    payments.sort(key=lambda x: x["date"])
    upcoming_payments = payments[:2]
    if upcoming_payments:
        message = "Ближайшие платежи:\n" + "\n".join(
            f"{p['date']}: {p['payment']} руб. (основной долг: {p['principal']}, проценты: {p['interest']})"
            for p in upcoming_payments
        )
        await update.message.reply_text(message)
    else:
        await update.message.reply_text("Нет предстоящих платежей.")