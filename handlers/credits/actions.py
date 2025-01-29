from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters
import datetime  # Импортируем datetime для проверки формата даты
from datetime import date
import logging
logging.basicConfig(level=logging.INFO)

# Этапы диалога
ASK_BANK, ASK_CATEGORY, ASK_AMOUNT, ASK_RATE, ASK_TERM, ASK_DAY, ASK_DATE = range(7)

BANKS = [["🟢 Сбербанк", "🔴 Альфа-Банк"], ["🟡 Тинькофф", "🔵 ВТБ"], ["🔵 Газпромбанк", "🟡 Райффайзенбанк"], ["Назад"]]
CATEGORIES = [["Ипотека", "Автокредит"], ["Кредит наличными", "Кредитная карта"], ["Назад"]]

# Функция для расчета ежемесячного платежа
def calculate_monthly_payment(loan_amount, interest_rate, loan_term):
    monthly_interest_rate = interest_rate / 100 / 12
    monthly_payment = (loan_amount * monthly_interest_rate) / (1 - (1 + monthly_interest_rate) ** -loan_term)
    return monthly_payment

async def delete_credit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удаляет выбранный кредит."""
    loans = context.user_data.get("loans", [])
    if not loans:
        await update.message.reply_text("У вас пока нет добавленных кредитов для удаления.")
        return ConversationHandler.END

    # Формируем список кредитов с индексами
    loan_list = "\n".join([f"{i + 1}. {loan['name']}" for i, loan in enumerate(loans)])
    await update.message.reply_text(f"Выберите номер кредита для удаления:\n\n{loan_list}")
    return 1  # Состояние для выбора кредита

async def confirm_delete_credit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Подтверждает удаление выбранного кредита."""
    try:
        credit_index = int(update.message.text) - 1
        loans = context.user_data.get("loans", [])
        if credit_index < 0 or credit_index >= len(loans):
            raise ValueError
        deleted_loan = loans.pop(credit_index)
        context.user_data["loans"] = loans
        await update.message.reply_text(f"Кредит {deleted_loan['name']} успешно удалён.")
    except (ValueError, IndexError):
        await update.message.reply_text("Некорректный номер. Пожалуйста, введите корректный номер кредита.")
        return 1  # Остаёмся в состоянии удаления
    return ConversationHandler.END

async def payment_schedule(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отображает график платежей по кредитам с выборкой платежей."""
    loans = context.user_data.get("loans", [])
    if not loans:
        await update.message.reply_text("У вас пока нет добавленных кредитов.")
        return

    current_date = datetime.date.today()
    schedules = []

    for loan in loans:
        try:
            # Проверка данных кредита
            if not all(key in loan for key in ['rate', 'amount', 'term', 'date']):
                raise KeyError(f"Отсутствуют данные для кредита {loan['name']}")

            # Рассчитываем ежемесячный платёж
            monthly_rate = loan['rate'] / 100 / 12
            monthly_payment = (loan['amount'] * monthly_rate) / (1 - (1 + monthly_rate) ** -loan['term'])
            payment_date = loan['date']

            # Генерация всех платежей
            payments = []
            for i in range(loan['term']):
                payments.append({
                    "date": payment_date,
                    "payment": monthly_payment,
                    "number": i + 1,
                })
                # Увеличиваем дату на 1 месяц
                next_month = payment_date.month + 1 if payment_date.month < 12 else 1
                next_year = payment_date.year + 1 if next_month == 1 else payment_date.year
                payment_date = payment_date.replace(year=next_year, month=next_month)

            # Формируем выборку платежей
            selected_payments = (
                payments[:3] +  # Первые 3 платежа
                [p for p in payments if p["date"] < current_date][-2:] +  # 2 платежа до текущего месяца
                [p for p in payments if p["date"] == current_date][:1] +  # Текущий платёж
                [p for p in payments if p["date"] > current_date][:1] +  # Следующий платёж
                payments[-3:]  # Последние 3 платежа
            )

            # Формируем текст для вывода
            loan_schedule = f"Кредит: {loan['name']} ({loan['bank']} | {loan['category']}):\n"
            previous_date = None
            for p in selected_payments:
                if previous_date and (p["date"] - previous_date).days > 35:
                    loan_schedule += "...\n"  # Визуальный разрыв между не соседними месяцами
                loan_schedule += (
                f"№{p['number']} | 📆 Дата: {p['date']} | 💳 Платёж: {p['payment']:,.2f} руб.\n"                )
                previous_date = p["date"]

            schedules.append(loan_schedule)

        except KeyError:
            schedules.append(f"Ошибка в данных кредита: {loan.get('name', 'Без имени')}.")

    # Отправляем результат
    result = "\n\n".join(schedules)
    await update.message.reply_text(f"Ваш график платежей:\n\n{result}")
    return ConversationHandler.END

async def view_credits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отображает список кредитов."""
    loans = context.user_data.get("loans", [])
    if not loans:
        await update.message.reply_text("У вас пока нет добавленных кредитов.")
    else:
        loan_list = "\n\n".join(
            [f"Кредит {i+1}:\n"
             f"{loan['name']}\n"
             f"💰 *Сумма:* {format(loan['amount'], ',')} руб.\n"
             f"📈 *Ставка:* {loan['rate']}%\n"
             f"🕒 *Срок:* {loan['term']} месяцев\n"
             f"📅 *Ежемесячный платёж:* {format(calculate_monthly_payment(loan['amount'], loan['rate'], loan['term']), ',.2f')} руб.\n"
             f"📆 *День платежа:* {loan['payment_day']}\n"
             f"⏳ *Дата первого платежа:* {loan['date']}"
             for i, loan in enumerate(loans)]
        )
        await update.message.reply_text(
            f"Ваши кредиты:\n\n{loan_list}",
            parse_mode="Markdown"  # parse_mode здесь
        )
        
async def start_add_credit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало процесса добавления кредита."""
    keyboard = ReplyKeyboardMarkup(BANKS, resize_keyboard=True)
    await update.message.reply_text("Выберите банк из списка:", reply_markup=keyboard)
    return ASK_BANK

async def ask_bank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняет выбор банка и предлагает выбрать категорию кредита."""
    context.user_data["bank"] = update.message.text
    logging.info(f"Выбран банк: {context.user_data['bank']}")
    keyboard = ReplyKeyboardMarkup(CATEGORIES, resize_keyboard=True)
    await update.message.reply_text("Выберите категорию кредита:", reply_markup=keyboard)
    return ASK_CATEGORY

async def ask_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняет выбор категории и спрашивает сумму кредита."""
    context.user_data["category"] = update.message.text
    logging.info(f"Выбрана категория: {context.user_data['category']}")
    await update.message.reply_text("Введите сумму кредита:")
    return ASK_AMOUNT

async def ask_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняет сумму кредита и спрашивает процентную ставку."""
    try:
        context.user_data["amount"] = float(update.message.text)
        await update.message.reply_text("Введите процентную ставку (например, 12.5):")
        return ASK_RATE
    except ValueError:
        await update.message.reply_text("Некорректная сумма. Пожалуйста, введите число:")
        return ASK_AMOUNT

async def ask_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняет процентную ставку и спрашивает срок кредита."""
    try:
        context.user_data["rate"] = float(update.message.text)
        await update.message.reply_text("Введите срок кредита в месяцах:")
        return ASK_TERM
    except ValueError:
        await update.message.reply_text("Некорректная ставка. Пожалуйста, введите число:")
        return ASK_RATE

async def ask_term(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняет срок кредита и спрашивает день платежа."""
    try:
        context.user_data["term"] = int(update.message.text)
        await update.message.reply_text("Введите день платежа (число от 1 до 28):")
        return ASK_DAY
    except ValueError:
        await update.message.reply_text("Некорректный срок. Пожалуйста, введите целое число:")
        return ASK_TERM

async def ask_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняет день платежа и спрашивает дату первого платежа."""
    try:
        day = int(update.message.text)
        if day < 1 or day > 28:
            raise ValueError
        context.user_data["payment_day"] = day
        await update.message.reply_text("Введите дату первого платежа (в формате ГГГГ-ММ-ДД):")
        return ASK_DATE
    except ValueError:
        await update.message.reply_text("Некорректный день платежа. Введите число от 1 до 28:")
        return ASK_DAY

async def ask_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняет дату первого платежа, завершает процесс добавления кредита."""
    try:
        date_input = update.message.text
        # Проверяем формат даты
        payment_date = datetime.datetime.strptime(date_input, "%Y-%m-%d").date()
        context.user_data["date"] = payment_date

        # Составляем название кредита
        credit_name = f"{context.user_data['category']} | {context.user_data['bank']} | {context.user_data['payment_day']} число | {context.user_data['amount']:,} руб."

        # Вычисляем ежемесячный платеж
        monthly_payment = calculate_monthly_payment(context.user_data["amount"], context.user_data["rate"], context.user_data["term"])

        
        # Сохраняем данные кредита
        credit = {
            "name": credit_name,
            "bank": context.user_data["bank"],
            "category": context.user_data["category"],
            "amount": context.user_data["amount"],
            "rate": context.user_data["rate"],
            "term": context.user_data["term"],
            "payment_day": context.user_data["payment_day"],
            "date": context.user_data["date"],
        }
        if "loans" not in context.user_data:
            context.user_data["loans"] = []
        context.user_data["loans"].append(credit)

        await update.message.reply_text(
            "Кредит успешно добавлен!\n\n"
            f"📌 *Название:* {credit['name']}\n"
            f"🏦 *Банк:* {credit['bank']}\n"
            f"💰 *Сумма:* {format(credit['amount'], ',')} руб.\n"
            f"📈 *Ставка:* {credit['rate']}%\n"
            f"🕒 *Срок:* {credit['term']} месяцев\n"
            f"📅 *Ежемесячный платеж:* {format(monthly_payment, ',.2f')} руб.\n"
            f"📆 *День платежа:* {credit['payment_day']}\n"
            f"⏳ *Дата первого платежа:* {credit['date']}",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup(CREDITS_MENU, resize_keyboard=True),
        )
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Некорректный формат даты. Пожалуйста, введите дату в формате ГГГГ-ММ-ДД:")
        return ASK_DATE

# Этапы диалога для расчета остатка
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


        if salary_day > current_day:
            next_salary_date = date(current_year, current_month, salary_day)
        else:
            next_month = current_month + 1 if current_month < 12 else 1
            next_year = current_year + 1 if next_month == 1 else current_year
            next_salary_date = date(next_year, next_month, salary_day)

        days_until_salary = (next_salary_date - current_date).days
        if days_until_salary <=0 :
          await update.message.reply_text("Вы ввели некорректную дату зарплаты. Попробуйте еще раз")
          return ASK_SALARY_DAY

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
    """Cancels and ends the conversation."""
    update.message.reply_text("Действие отменено.")
    return ConversationHandler.END


def daily_balance_handler():
    """Создает ConversationHandler для расчета остатка денег на день."""
    conv_handler = ConversationHandler(
        entry_points=[
            MessageHandler(filters.Regex("^Расчет остатка$"), calculate_daily_balance_start),
        ],
        states={
            ASK_BALANCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_balance)],
            ASK_SALARY_DAY: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_salary_day)],
        },
        fallbacks=[CommandHandler("cancel", cancel)]
    )
    return conv_handler