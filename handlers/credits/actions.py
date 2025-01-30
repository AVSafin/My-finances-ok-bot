from telegram import Update, ReplyKeyboardMarkup
from storage import Storage

storage = Storage()
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters
import datetime
import logging
from constants import BANKS, CATEGORIES

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
        return

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

            # Подсчет оставшихся платежей
            passed_months = 0
            temp_date = payment_date
            while temp_date <= current_date:
                passed_months += 1
                next_month = temp_date.month % 12 + 1
                next_year = temp_date.year + (temp_date.month == 12)
                temp_date = temp_date.replace(year=next_year, month=next_month)

            remaining_payments = loan['term'] - passed_months
            if remaining_payments < 0:
                remaining_payments = 0

            # Расчет остатков
            total_payment = monthly_payment * loan['term']
            total_interest = total_payment - loan['amount']
            
            remaining_total = monthly_payment * remaining_payments
            remaining_principal = loan['amount'] * (remaining_payments / loan['term'])
            remaining_interest = remaining_total - remaining_principal

            # Формирование графика платежей
            payments = []
            current_payment_date = payment_date
            for i in range(loan['term']):
                payments.append({
                    "date": current_payment_date,
                    "payment": monthly_payment,
                    "number": i + 1
                })
                next_month = current_payment_date.month % 12 + 1
                next_year = current_payment_date.year + (current_payment_date.month == 12)
                current_payment_date = current_payment_date.replace(year=next_year, month=next_month)

            # Формируем текст для вывода
            loan_schedule = (
                f"Кредит: {loan['name']} ({loan['bank']} | {loan['category']}):\n"
                f"💰 Остаток основного долга: {remaining_principal:,.2f} руб.\n"
                f"📈 Остаток процентов: {remaining_interest:,.2f} руб.\n\n"
            )
            
            # Выбираем платежи для отображения
            selected_payments = []
            selected_payments.extend(payments[:3])  # Первые 3 платежа
            
            # Добавляем 2 платежа до текущего месяца
            past_payments = [p for p in payments if p["date"] < current_date][-2:]
            if past_payments:
                if selected_payments[-1]["number"] < past_payments[0]["number"] - 1:
                    loan_schedule += "...\n"
                selected_payments.extend(past_payments)
            
            # Добавляем текущий и следующий платежи
            current_and_next = ([p for p in payments if p["date"] == current_date] +
                              [p for p in payments if p["date"] > current_date])[:2]
            if current_and_next:
                if selected_payments[-1]["number"] < current_and_next[0]["number"] - 1:
                    loan_schedule += "...\n"
                selected_payments.extend(current_and_next)
            
            # Добавляем последние 3 платежа
            last_payments = payments[-3:]
            if last_payments:
                if selected_payments[-1]["number"] < last_payments[0]["number"] - 1:
                    loan_schedule += "...\n"
                selected_payments.extend(last_payments)

            # Удаляем дубликаты и сортируем по номеру
            seen = set()
            selected_payments = [p for p in selected_payments 
                               if p["number"] not in seen and not seen.add(p["number"])]
            selected_payments.sort(key=lambda x: x["number"])

            # Формируем вывод платежей
            previous_number = 0
            for p in selected_payments:
                if p["number"] > previous_number + 1:
                    loan_schedule += "...\n"
                # Расчет остатков для каждого платежа
                payments_left = loan['term'] - p['number'] + 1
                remaining_principal = loan['amount'] * (payments_left / loan['term'])
                remaining_interest = (p['payment'] * payments_left) - remaining_principal
                
                loan_schedule += (
                    f"№{p['number']} | 📆 {p['date']} | 💳 {p['payment']:,.2f} руб. | "
                    f"💵 Тело: {remaining_principal:,.2f} руб. | 💹 Проценты: {remaining_interest:,.2f} руб.\n"
                )
                previous_number = p["number"]

            schedules.append(loan_schedule)

        except Exception as e:
            schedules.append(f"Ошибка в данных кредита {loan.get('name', 'Без имени')}: {str(e)}")

    # Отправляем результат
    result = "\n\n".join(schedules)
    await update.message.reply_text(f"Ваш график платежей:\n\n{result}")

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
            
            # Преобразуем дату если она строка
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
                next_month = payment_date.month + 1 if payment_date.month < 12 else 1
                next_year = payment_date.year + 1 if next_month == 1 else payment_date.year
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

        except KeyError:
            schedules.append(f"Ошибка в данных кредита: {loan.get('name', 'Без имени')}.")

    # Отправляем результат
    result = "\n\n".join(schedules)
    await update.message.reply_text(f"Ваш график платежей:\n\n{result}")
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