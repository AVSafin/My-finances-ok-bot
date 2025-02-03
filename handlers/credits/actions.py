from telegram import Update, ReplyKeyboardMarkup
from storage import Storage

storage = Storage()
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters
import datetime
import logging
from constants import (
    BANKS, 
    CATEGORIES, 
    CREDIT_MODIFICATION_MENU,
    CREDIT_PARAMETERS_MENU,
    CREDIT_REPAYMENT_MENU
)

# Этапы диалога для кредитов
ASK_BANK, ASK_CATEGORY, ASK_AMOUNT, ASK_RATE, ASK_TERM, ASK_DAY, ASK_DATE = range(7)

# Функция для расчета ежемесячного платежа
def calculate_monthly_payment(loan_amount, interest_rate, loan_term):
    monthly_interest_rate = interest_rate / 100 / 12
    monthly_payment = (loan_amount * monthly_interest_rate) / (1 - (1 + monthly_interest_rate) ** -loan_term)
    return monthly_payment

async def delete_credit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удаляет выбранный кредит."""
    user_data = storage.get_user_data(str(update.effective_user.id))
    loans = user_data.get("loans", [])
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
        user_data = storage.get_user_data(str(update.effective_user.id))
        loans = user_data.get("loans", [])
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
    """Отображает ближайшие платежи по кредитам, сгруппированные по датам."""
    user_data = storage.get_user_data(str(update.effective_user.id))
    loans = user_data.get("loans", [])
    if not loans:
        await update.message.reply_text("У вас пока нет добавленных кредитов.")
        return ConversationHandler.END

    current_date = datetime.date.today()
    upcoming_payments = {}  # Словарь для группировки платежей по датам

    for loan in loans:
        try:
            # Расчет ежемесячного платежа
            monthly_rate = loan['rate'] / 100 / 12
            monthly_payment = (loan['amount'] * monthly_rate) / (1 - (1 + monthly_rate) ** -loan['term'])

            # Преобразование даты из строки в объект date, если нужно
            if isinstance(loan['date'], str):
                payment_date = datetime.datetime.strptime(loan['date'], '%Y-%m-%d').date()
            else:
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
                next_month = payment_date.month + 1
                next_year = payment_date.year
                if next_month > 12:
                    next_month = 1
                    next_year += 1
                payment_date = payment_date.replace(year=next_year, month=next_month)

            # Находим следующий платеж
            next_payments = [p for p in payments if p["date"] >= current_date]
            if next_payments:
                next_payment = next_payments[0]
                remaining_payments = len(next_payments)
                remaining_total = monthly_payment * remaining_payments
                remaining_principal = loan['amount'] * (remaining_payments / loan['term'])
                remaining_interest = remaining_total - remaining_principal

                payment_info = {
                    'name': loan['name'],
                    'payment': monthly_payment,
                    'remaining_payments': remaining_payments,
                    'remaining_principal': remaining_principal,
                    'remaining_interest': remaining_interest
                }

                # Группируем платежи по датам
                if next_payment["date"] in upcoming_payments:
                    upcoming_payments[next_payment["date"]].append(payment_info)
                else:
                    upcoming_payments[next_payment["date"]] = [payment_info]

        except KeyError as e:
            logging.error(f"Ошибка в данных кредита {loan.get('name', 'Без имени')}: {str(e)}")
            continue

    # Формируем вывод сгруппированных платежей
    result = "📅 Ближайшие платежи по кредитам:\n\n"

    # Сортируем даты
    sorted_dates = sorted(upcoming_payments.keys())
    for payment_date in sorted_dates[:3]:  # Показываем только 3 ближайшие даты
        result += f"🗓 {payment_date.strftime('%d.%m.%Y')}:\n"
        total_payment_for_date = 0

        for payment_info in upcoming_payments[payment_date]:
            total_payment_for_date += payment_info['payment']
            result += (
                f"• {payment_info['name']}\n"
                f"  💳 Платёж: {payment_info['payment']:,.2f} руб.\n"
                f"  📊 Осталось платежей: {payment_info['remaining_payments']}\n"
                f"  💰 Остаток долга: {payment_info['remaining_principal']:,.2f} руб.\n"
                f"  💹 Остаток процентов: {payment_info['remaining_interest']:,.2f} руб.\n"
            )

        result += f"📌 Всего к оплате {payment_date.strftime('%d.%m')}: {total_payment_for_date:,.2f} руб.\n\n"

    await update.message.reply_text(result)
    return ConversationHandler.END

async def view_credits(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отображает список кредитов."""
    user_data = storage.get_user_data(str(update.effective_user.id))
    loans = user_data.get("loans", [])
    if not loans:
        await update.message.reply_text("У вас пока нет добавленных кредитов.")
    else:
        current_date = datetime.date.today()
        loan_list = []
        for i, loan in enumerate(loans):
            monthly_payment = calculate_monthly_payment(loan['amount'], loan['rate'], loan['term'])
            payment_date = datetime.datetime.strptime(str(loan['date']), '%Y-%m-%d').date() if isinstance(loan['date'], str) else loan['date']
            passed_months = sum(1 for m in range(loan['term']) if payment_date.replace(month=((payment_date.month-1+m)%12)+1, year=payment_date.year + (payment_date.month+m-1)//12) <= current_date)
            remaining_payments = max(0, loan['term'] - passed_months)
            remaining_total = monthly_payment * remaining_payments
            remaining_principal = loan['amount'] * (remaining_payments / loan['term'])
            remaining_interest = remaining_total - remaining_principal

            loan_info = (
                f"Кредит {i+1}:\n"
                f"{loan['name']}\n"
                f"💰 *Сумма:* {format(loan['amount'], ',')} руб.\n"
                f"📈 *Ставка:* {loan['rate']}%\n"
                f"🕒 *Срок:* {loan['term']} месяцев\n"
                f"📅 *Ежемесячный платёж:* {format(monthly_payment, ',.2f')} руб.\n"
                f"📆 *День платежа:* {loan['payment_day']}\n"
                f"⏳ *Дата первого платежа:* {loan['date']}\n"
                f"💵 *Остаток основного долга:* {format(remaining_principal, ',.2f')} руб.\n"
                f"💹 *Остаток процентов:* {format(remaining_interest, ',.2f')} руб."
            )
            loan_list.append(loan_info)
        loan_list = "\n\n".join(loan_list)
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
        user_id = str(update.effective_user.id)
        user_data = storage.get_user_data(user_id)
        if "loans" not in user_data:
            user_data["loans"] = []
        user_data["loans"].append(credit)
        storage.save_user_data(user_id, user_data)

        await update.message.reply_text(
            "Кредит успешно добавлен!\n\n"
            f"📌 *Название:* {credit['name']}\n"
            f"🏦 *Банк:* {credit['bank']}\n"
            f"💰 *Сумма:* {format(credit['amount'], ',')} руб.\n"
            f"📈 *Ставка:* {credit['rate']}%\n"
            f"🕒 *Срок:* {credit['term']} месяцев\n"
            f"📅 *Ежемесячный платеж:* {format(monthly_payment, ',.2f')} руб.\n"
            f"📆 *День платежа:* {credit['payment_day']}\n"
            f"⏳ *Дата первого платежа:* {credit['date']}\n\n"
            f"💵 *Остаток основного долга:* {format(credit['amount'] * ((credit['term'] - len([p for p in range(credit['term']) if datetime.datetime.strptime(credit['date'], '%Y-%m-%d').date().replace(day=credit['payment_day']) + datetime.timedelta(days=30*p) <= datetime.date.today()])) / credit['term']), ',.2f')} руб.\n"
            f"💹 *Остаток процентов:* {format(monthly_payment * (credit['term'] - len([p for p in range(credit['term']) if datetime.datetime.strptime(credit['date'], '%Y-%m-%d').date().replace(day=credit['payment_day']) + datetime.timedelta(days=30*p) <= datetime.date.today()])) - (credit['amount'] * ((credit['term'] - len([p for p in range(credit['term']) if datetime.datetime.strptime(credit['date'], '%Y-%m-%d').date().replace(day=credit['payment_day']) + datetime.timedelta(days=30*p) <= datetime.date.today()])) / credit['term'])), ',.2f')} руб.",
            parse_mode="Markdown",
            reply_markup=ReplyKeyboardMarkup(CATEGORIES, resize_keyboard=True),
        )
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Некорректный формат даты. Пожалуйста, введите дату в формате ГГГГ-ММ-ДД:")
        return ASK_DATE
# States for credit modification
(CHOOSE_CREDIT, CHOOSE_ACTION, ASK_NEW_PAYMENT_DAY, ASK_CHANGE_DATE, ASK_REPAYMENT_AMOUNT, 
 CONFIRM_CHANGES, CHOOSE_PARAMETER, ASK_NEW_AMOUNT, ASK_NEW_RATE, ASK_NEW_TERM, 
 ASK_NEW_PAYMENT_AMOUNT, ASK_NEW_PAYMENT_DATE, ASK_NEW_BALANCE) = range(13)

async def modify_credit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Starts credit modification process."""
    user_data = storage.get_user_data(str(update.effective_user.id))
    loans = user_data.get("loans", [])
    if not loans:
        await update.message.reply_text("У вас пока нет добавленных кредитов для изменения.")
        return ConversationHandler.END

    # Create buttons for each credit
    credit_buttons = [[loan['name']] for loan in loans]
    credit_buttons.append(["Назад"])
    keyboard = ReplyKeyboardMarkup(credit_buttons, resize_keyboard=True)
    await update.message.reply_text("Выберите кредит для изменения:", reply_markup=keyboard)
    return CHOOSE_CREDIT

async def handle_credit_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles credit selection and shows modification options."""
    user_data = storage.get_user_data(str(update.effective_user.id))
    loans = user_data.get("loans", [])
    selected_name = update.message.text

    # Find the credit by name
    for index, loan in enumerate(loans):
        if loan['name'] == selected_name:
            context.user_data['selected_credit_index'] = index
            keyboard = ReplyKeyboardMarkup(CREDIT_MODIFICATION_MENU, resize_keyboard=True)
            await update.message.reply_text("Выберите действие:", reply_markup=keyboard)
            return CHOOSE_ACTION

    await update.message.reply_text("Кредит не найден. Пожалуйста, выберите кредит из списка.")
    return CHOOSE_CREDIT

async def handle_action_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles modification action selection."""
    action = update.message.text
    if action == "Досрочное погашение":
        keyboard = ReplyKeyboardMarkup(CREDIT_REPAYMENT_MENU, resize_keyboard=True)
        await update.message.reply_text("Выберите вариант досрочного погашения:", reply_markup=keyboard)
        return ASK_REPAYMENT_AMOUNT
    elif action == "Изменение даты платежа":
        await update.message.reply_text("Введите новый день платежа (число от 1 до 28):")
        return ASK_NEW_PAYMENT_DAY
    elif action == "Изменение параметров":
        keyboard = ReplyKeyboardMarkup(CREDIT_PARAMETERS_MENU, resize_keyboard=True)
        await update.message.reply_text("Выберите параметр для изменения:", reply_markup=keyboard)
        return CHOOSE_PARAMETER
    else:
        return ConversationHandler.END

async def handle_parameter_choice(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles parameter choice for modification."""
    choice = update.message.text
    if choice == "Изменить сумму":
        await update.message.reply_text("Введите новую сумму кредита:")
        return ASK_NEW_AMOUNT
    elif choice == "Изменить ставку":
        await update.message.reply_text("Введите новую процентную ставку:")
        return ASK_NEW_RATE
    elif choice == "Изменить срок":
        await update.message.reply_text("Введите новый срок кредита в месяцах:")
        return ASK_NEW_TERM
    elif choice == "Изменить платёж":
        await update.message.reply_text("Введите новую сумму ежемесячного платежа:")
        return ASK_NEW_PAYMENT_AMOUNT
    elif choice == "Изменить остаток":
        await update.message.reply_text("Введите текущий остаток по кредиту:")
        return ASK_NEW_BALANCE
    else:
        return ConversationHandler.END

async def handle_new_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles new loan amount input."""
    try:
        new_amount = float(update.message.text)
        if new_amount <= 0:
            raise ValueError("Отрицательная сумма")

        user_id = str(update.effective_user.id)
        user_data = storage.get_user_data(user_id)
        credit_index = context.user_data['selected_credit_index']
        loan = user_data['loans'][credit_index]

        # Update loan amount
        loan['amount'] = new_amount

        # Recalculate monthly payment
        monthly_rate = loan['rate'] / 100 / 12
        monthly_payment = (new_amount * monthly_rate) / (1 - (1 + monthly_rate) ** -loan['term'])

        user_data['loans'][credit_index] = loan
        storage.update_user_data(user_id, user_data)

        await update.message.reply_text(
            f"Сумма кредита успешно обновлена!\n"
            f"Новая сумма: {new_amount:,.2f} руб.\n"
            f"Новый ежемесячный платеж: {monthly_payment:,.2f} руб."
        )
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Некорректная сумма. Пожалуйста, введите положительное число:")
        return ASK_NEW_AMOUNT

async def handle_new_term(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles new loan term input."""
    try:
        new_term = int(update.message.text)
        if new_term <= 0:
            raise ValueError("Некорректный срок")

        user_id = str(update.effective_user.id)
        user_data = storage.get_user_data(user_id)
        credit_index = context.user_data['selected_credit_index']
        loan = user_data['loans'][credit_index]

        # Update loan term
        loan['term'] = new_term

        # Recalculate monthly payment
        monthly_rate = loan['rate'] / 100 / 12
        monthly_payment = (loan['amount'] * monthly_rate) / (1 - (1 + monthly_rate) ** -new_term)

        user_data['loans'][credit_index] = loan
        storage.update_user_data(user_id, user_data)

        await update.message.reply_text(
            f"Срок кредита успешно обновлен!\n"
            f"Новый срок: {new_term} месяцев\n"
            f"Новый ежемесячный платеж: {monthly_payment:,.2f} руб."
        )
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Некорректный срок. Пожалуйста, введите положительное целое число:")
        return ASK_NEW_TERM

async def handle_new_rate(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles new interest rate input."""
    try:
        new_rate = float(update.message.text)
        if new_rate <= 0:
            raise ValueError("Отрицательная ставка")

        user_id = str(update.effective_user.id)
        user_data = storage.get_user_data(user_id)
        credit_index = context.user_data['selected_credit_index']
        loan = user_data['loans'][credit_index]

        # Update loan rate
        loan['rate'] = new_rate

        # Recalculate monthly payment
        monthly_rate = new_rate / 100 / 12
        monthly_payment = (loan['amount'] * monthly_rate) / (1 - (1 + monthly_rate) ** -loan['term'])

        user_data['loans'][credit_index] = loan
        storage.update_user_data(user_id, user_data)

        await update.message.reply_text(
            f"Процентная ставка успешно обновлена!\n"
            f"Новая ставка: {new_rate:.2f}%\n"
            f"Новый ежемесячный платеж: {monthly_payment:,.2f} руб."
        )
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Некорректная ставка. Пожалуйста, введите положительное число:")
        return ASK_NEW_RATE

async def handle_new_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles new loan balance input."""
    try:
        new_balance = float(update.message.text)
        if new_balance <= 0:
            raise ValueError("Отрицательный остаток")

        user_id = str(update.effective_user.id)
        user_data = storage.get_user_data(user_id)
        credit_index = context.user_data['selected_credit_index']
        loan = user_data['loans'][credit_index]

        # Update loan balance
        loan['amount'] = new_balance

        # Recalculate monthly payment
        monthly_rate = loan['rate'] / 100 / 12
        monthly_payment = (loan['amount'] * monthly_rate) / (1 - (1 + monthly_rate) ** -loan['term'])

        user_data['loans'][credit_index] = loan
        storage.update_user_data(user_id, user_data)

        await update.message.reply_text(
            f"Остаток по кредиту успешно обновлен!\n"
            f"Новый остаток: {new_balance:,.2f} руб.\n"
            f"Новый ежемесячный платеж: {monthly_payment:,.2f} руб."
        )
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Некорректная сумма. Пожалуйста, введите положительное число:")
        return ASK_NEW_BALANCE

        user_id = str(update.effective_user.id)
        user_data = storage.get_user_data(user_id)
        credit_index = context.user_data['selected_credit_index']
        loan = user_data['loans'][credit_index]

        # Сохраняем новый остаток
        loan['amount'] = new_balance

        # Пересчитываем ежемесячный платеж
        monthly_rate = loan['rate'] / 100 / 12
        monthly_payment = (new_balance * monthly_rate) / (1 - (1 + monthly_rate) ** -loan['term'])

        user_data['loans'][credit_index] = loan
        storage.update_user_data(user_id, user_data)

        await update.message.reply_text(
            f"Остаток по кредиту успешно обновлен!\n"
            f"Новый остаток: {new_balance:,.2f} руб.\n"
            f"Новый ежемесячный платеж: {monthly_payment:,.2f} руб."
        )
        return ConversationHandler.END
    except ValueError as e:
        await update.message.reply_text("Некорректная сумма. Пожалуйста, введите положительное число:")
        return ASK_NEW_BALANCE

async def handle_new_payment_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles new payment amount input."""
    try:
        new_payment = float(update.message.text)
        context.user_data['new_payment'] = new_payment
        await update.message.reply_text("Введите дату, с которой будет действовать новый платеж (ГГГГ-ММ-ДД):")
        return ASK_NEW_PAYMENT_DATE
    except ValueError:
        await update.message.reply_text("Некорректная сумма. Пожалуйста, введите число:")
        return ASK_NEW_PAYMENT_AMOUNT

async def handle_new_payment_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the date from which the new payment will be effective."""
    try:
        new_date = datetime.datetime.strptime(update.message.text, "%Y-%m-%d").date()
        user_id = str(update.effective_user.id)
        user_data = storage.get_user_data(user_id)
        credit_index = context.user_data['selected_credit_index']

        # Обновляем параметры кредита с учетом нового платежа
        loan = user_data['loans'][credit_index]
        new_payment = context.user_data['new_payment']

        # Пересчитываем параметры кредита
        monthly_rate = loan['rate'] / 100 / 12
        remaining_months = loan['term']
        loan['amount'] = (new_payment * (1 - (1 + monthly_rate) ** -remaining_months)) / monthly_rate

        user_data['loans'][credit_index] = loan
        storage.update_user_data(user_id, user_data)

        await update.message.reply_text(
            f"Платеж успешно изменен!\n"
            f"Новый платеж: {new_payment:,.2f} руб.\n"
            f"Действует с: {new_date.strftime('%Y-%m-%d')}\n"
            f"Пересчитанная сумма кредита: {loan['amount']:,.2f} руб."
        )
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Некорректный формат даты. Используйте формат ГГГГ-ММ-ДД:")
        return ASK_NEW_PAYMENT_DATE

async def handle_new_parameters(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles new credit parameters input."""
    try:
        params = update.message.text.split(',')
        if len(params) != 3:
            raise ValueError("Неверное количество параметров")

        new_amount = float(params[0])
        new_rate = float(params[1])
        new_term = int(params[2])

        if new_amount <= 0 or new_rate <= 0 or new_term <= 0:
            raise ValueError("Параметры должны быть положительными числами")

        user_id = str(update.effective_user.id)
        user_data = storage.get_user_data(user_id)
        credit_index = context.user_data['selected_credit_index']
        loan = user_data['loans'][credit_index]

        # Обновляем параметры кредита
        loan['amount'] = new_amount
        loan['rate'] = new_rate
        loan['term'] = new_term

        # Рассчитываем новый ежемесячный платеж
        monthly_rate = new_rate / 100 / 12
        monthly_payment = (new_amount * monthly_rate) / (1 - (1 + monthly_rate) ** -new_term)

        user_data['loans'][credit_index] = loan
        storage.update_user_data(user_id, user_data)

        await update.message.reply_text(
            f"Параметры кредита успешно обновлены!\n"
            f"Сумма: {new_amount:,.2f} руб.\n"
            f"Ставка: {new_rate}%\n"
            f"Срок: {new_term} месяцев\n"
            f"Новый ежемесячный платеж: {monthly_payment:,.2f} руб."
        )
        return ConversationHandler.END
    except ValueError as e:
        await update.message.reply_text(
            "Ошибка ввода. Убедитесь, что вы ввели три числа через запятую:\n"
            "Сумма,Ставка,Срок"
        )
        return ASK_NEW_PARAMETERS

async def handle_repayment_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles early repayment amount input."""
    try:
        repayment_type = update.message.text
        if repayment_type in ["Уменьшение срока", "Уменьшение платежа"]:
            context.user_data['repayment_type'] = repayment_type
            await update.message.reply_text("Введите сумму досрочного погашения:")
            return CONFIRM_CHANGES
        else:
            await update.message.reply_text("Пожалуйста, выберите вариант из меню.")
            return ASK_REPAYMENT_AMOUNT
    except ValueError:
        await update.message.reply_text("Некорректная сумма. Пожалуйста, введите число:")
        return ASK_REPAYMENT_AMOUNT

async def handle_new_payment_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles new payment day input."""
    try:
        newday = int(update.message.text)
        if new_day < 1 or new_day > 28:
            raise ValueError
        context.user_data['new_payment_day'] = new_day
        await update.message.reply_text("Введите дату, с которой будет действовать новый день платежа (ГГГГ-ММ-ДД):")
        return ASK_CHANGE_DATE
    except ValueError:
        await update.message.reply_text("Некорректный день. Введите число от 1 до 28:")
        return ASK_NEW_PAYMENT_DAY

async def handle_change_date(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handles the date from which the new payment day will be effective."""
    try:
        new_date = datetime.datetime.strptime(update.message.text, "%Y-%m-%d").date()
        user_id = str(update.effective_user.id)
        user_data = storage.get_user_data(user_id)
        credit_index = context.user_data['selected_credit_index']

        user_data['loans'][credit_index]['payment_day'] = context.user_data['new_payment_day']
        user_data['loans'][credit_index]['date'] = new_date

        storage.update_user_data(user_id, user_data)

        await update.message.reply_text(
            f"Дата платежа успешно изменена!\n"
            f"Новый день платежа: {context.user_data['new_payment_day']}\n"
            f"Действует с: {new_date.strftime('%Y-%m-%d')}"
        )
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Некорректный формат даты. Используйте формат ГГГГ-ММ-ДД:")
        return ASK_CHANGE_DATE

async def handle_confirm_changes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Confirms and applies early repayment changes."""
    try:
        repayment_amount = float(update.message.text)
        user_id = str(update.effective_user.id)
        user_data = storage.get_user_data(user_id)
        credit_index = context.user_data['selected_credit_index']
        loan = user_data['loans'][credit_index]

        monthly_payment = calculate_monthly_payment(loan['amount'], loan['rate'], loan['term'])

        if context.user_data['repayment_type'] == "Уменьшение срока":
            # Пересчитываем срок при том же платеже
            remaining_amount = loan['amount'] - repayment_amount
            new_term = int(remaining_amount * monthly_payment / (monthly_payment * loan['term']))
            loan['amount'] = remaining_amount
            loan['term'] = new_term
        else:  # Уменьшение платежа
            # Сохраняем срок, пересчитываем платеж
            loan['amount'] -= repayment_amount

        user_data['loans'][credit_index] = loan
        storage.update_user_data(user_id, user_data)

        new_payment = calculate_monthly_payment(loan['amount'], loan['rate'], loan['term'])

        await update.message.reply_text(
            f"Досрочное погашение выполнено успешно!\n"
            f"Сумма погашения: {repayment_amount:,.2f} руб.\n"
            f"Новый ежемесячный платеж: {new_payment:,.2f} руб.\n"
            f"Оставшийся срок: {loan['term']} месяцев"
        )
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Некорректная сумма. Пожалуйста, введите число:")
        return CONFIRM_CHANGES