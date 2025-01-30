from telegram import Update
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters
import datetime
from datetime import date

# Этапы диалога
ASK_BALANCE, ASK_SALARY_DAY = range(2)

async def calculate_daily_balance_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинает диалог для расчета остатка денег на день."""
    await update.message.reply_text("Введите ваш текущий остаток денежных средств:")
    return ASK_BALANCE

async def ask_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получает остаток денежных средств от пользователя."""
    try:
        balance = float(update.message.text)
        context.user_data["balance"] = balance
        await update.message.reply_text("Введите число месяца, когда у вас следующее начисление зарплаты (от 1 до 31):")
        return ASK_SALARY_DAY
    except ValueError:
        await update.message.reply_text("Некорректный формат суммы. Пожалуйста, введите число:")
        return ASK_BALANCE

async def ask_salary_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получает день начисления зарплаты и рассчитывает остаток."""
    try:
        salary_day = int(update.message.text)
        if salary_day < 1 or salary_day > 31:
            raise ValueError
        context.user_data["salary_day"] = salary_day

        balance = context.user_data["balance"]
        current_date = date.today()
        current_day = current_date.day
        current_month = current_date.month
        current_year = current_date.year

        # Определение даты следующего начисления зарплаты
        if salary_day > current_day:
            next_salary_date = date(current_year, current_month, salary_day)
        else:
            next_month = current_month + 1 if current_month < 12 else 1
            next_year = current_year + 1 if next_month == 1 else current_year
            next_salary_date = date(next_year, next_month, salary_day)

        days_until_salary = (next_salary_date - current_date).days
        if days_until_salary <= 0:
            await update.message.reply_text("Вы ввели некорректную дату зарплаты. Попробуйте еще раз")
            return ASK_SALARY_DAY

        # Расчет среднего остатка на день
        daily_balance = balance / days_until_salary
        await update.message.reply_text(
            f"Ваш средний остаток на день до зарплаты: {format(daily_balance, ',.2f')} руб.\n"
            f"До зарплаты {days_until_salary} дней."
        )
        return ConversationHandler.END

    except ValueError:
        await update.message.reply_text("Некорректный день. Введите число от 1 до 31:")
        return ASK_SALARY_DAY

def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отменяет и завершает разговор."""
    update.message.reply_text("Действие отменено.")
    return ConversationHandler.END

def daily_balance_handler():
    """Создает ConversationHandler для расчета остатка денег на день."""
    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^Рассчитать остаток на день$"), calculate_daily_balance_start),
        ],
        states={
            ASK_BALANCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_balance)],
            ASK_SALARY_DAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_salary_day)],
        },
        fallbacks=[MessageHandler(filters.Regex("^Отмена$"), cancel)]  # Фallback для отмены
    )
    return conv_handler