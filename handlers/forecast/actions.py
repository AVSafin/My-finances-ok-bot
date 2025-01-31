from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler, MessageHandler, filters
import datetime
from datetime import date
from storage import Storage

storage = Storage()

# Этапы диалога для регулярных расходов
ADD_EXPENSE_NAME, ADD_EXPENSE_AMOUNT, ADD_EXPENSE_DAY = range(3, 6)

async def start_add_expense(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинает диалог добавления регулярного расхода."""
    await update.message.reply_text("Введите название регулярного расхода (например: Аренда, Интернет):")
    return ADD_EXPENSE_NAME

async def add_expense_name(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получает название расхода."""
    context.user_data['temp_expense'] = {'name': update.message.text}
    await update.message.reply_text("Введите сумму расхода:")
    return ADD_EXPENSE_AMOUNT

async def add_expense_amount(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получает сумму расхода."""
    try:
        amount = float(update.message.text)
        context.user_data['temp_expense']['amount'] = amount
        await update.message.reply_text("Введите день месяца для расхода (1-31):")
        return ADD_EXPENSE_DAY
    except ValueError:
        await update.message.reply_text("Некорректная сумма. Пожалуйста, введите число:")
        return ADD_EXPENSE_AMOUNT

async def add_expense_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получает день расхода и сохраняет расход."""
    try:
        day = int(update.message.text)
        if day < 1 or day > 31:
            raise ValueError

        user_data = storage.get_user_data(str(update.effective_user.id))
        if 'regular_expenses' not in user_data:
            user_data['regular_expenses'] = []

        expense = context.user_data['temp_expense']
        expense['day'] = day
        user_data['regular_expenses'].append(expense)
        storage.update_user_data(str(update.effective_user.id), user_data)

        await update.message.reply_text(
            f"Регулярный расход добавлен:\n"
            f"📝 Название: {expense['name']}\n"
            f"💰 Сумма: {expense['amount']:,.2f} руб.\n"
            f"📅 День: {expense['day']}"
        )
        return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Некорректный день. Введите число от 1 до 31:")
        return ADD_EXPENSE_DAY


# Этапы диалога
ASK_BALANCE, ASK_SALARY_DAY = range(2)

async def calculate_daily_balance_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинает диалог для расчета остатка денег на день."""
    user_data = storage.get_user_data(str(update.effective_user.id))
    income_data = user_data.get('income', {})
    
    if 'main_salary_day' in income_data:
        context.user_data["salary_day"] = income_data['main_salary_day']
        await update.message.reply_text("Введите ваш текущий остаток денежных средств:")
        return ASK_BALANCE
    else:
        await update.message.reply_text("Введите ваш текущий остаток денежных средств:")
        return ASK_BALANCE

async def ask_balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получает остаток денежных средств от пользователя."""
    try:
        balance = float(update.message.text)
        context.user_data["balance"] = balance
        
        if "salary_day" in context.user_data:
            # Используем сохраненный день зарплаты
            return await ask_salary_day(update, context, skip_input=True)
        else:
            await update.message.reply_text("Введите число месяца, когда у вас следующее начисление зарплаты (от 1 до 31):")
            return ASK_SALARY_DAY
    except ValueError:
        await update.message.reply_text("Некорректный формат суммы. Пожалуйста, введите число:")
        return ASK_BALANCE

async def ask_salary_day(update: Update, context: ContextTypes.DEFAULT_TYPE, skip_input=False):
    """Получает день начисления зарплаты и рассчитывает остаток с учетом регулярных расходов."""
    try:
        if skip_input:
            salary_day = context.user_data["salary_day"]
        else:
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

        # Учет регулярных расходов
        user_data = storage.get_user_data(str(update.effective_user.id))
        regular_expenses = user_data.get('regular_expenses', [])
        total_expenses = 0
        expenses_text = ""

        for expense in regular_expenses:
            expense_day = expense['day']
            if (expense_day >= current_day and expense_day <= salary_day) or \
               (salary_day < current_day and (expense_day >= current_day or expense_day <= salary_day)):
                total_expenses += expense['amount']
                expenses_text += f"📌 {expense['name']}: {expense['amount']:,.2f} руб. ({expense['day']} числа)\n"

        # Расчет среднего остатка на день
        balance_after_expenses = balance - total_expenses
        daily_balance = balance_after_expenses / days_until_salary

        result = (
            f"💰 Текущий баланс: {balance:,.2f} руб.\n"
            f"📊 Регулярные расходы до зарплаты:\n{expenses_text if expenses_text else '(нет регулярных расходов)'}\n"
            f"💵 Баланс после расходов: {balance_after_expenses:,.2f} руб.\n"
            f"📅 Средний остаток на день: {daily_balance:,.2f} руб.\n"
            f"⏳ До зарплаты: {days_until_salary} дней"
        )

        await update.message.reply_text(result)
        return ConversationHandler.END

    except ValueError:
        await update.message.reply_text("Некорректный день. Введите число от 1 до 31:")
        return ASK_SALARY_DAY

async def view_regular_expenses(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отображает список регулярных расходов."""
    user_data = storage.get_user_data(str(update.effective_user.id))
    regular_expenses = user_data.get('regular_expenses', [])

    if not regular_expenses:
        await update.message.reply_text("У вас пока нет добавленных регулярных расходов.")
        return

    result = "📋 Ваши регулярные расходы:\n\n"
    total = 0
    for expense in regular_expenses:
        result += (f"📌 {expense['name']}\n"
                  f"💰 Сумма: {expense['amount']:,.2f} руб.\n"
                  f"📅 День: {expense['day']}\n\n")
        total += expense['amount']

    result += f"Общая сумма расходов: {total:,.2f} руб."
    await update.message.reply_text(result)

async def cancel(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
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
# Этапы диалога для управления доходами
INCOME_MENU, ADD_MAIN_INCOME, ADD_MAIN_INCOME_DAY, ADD_ADVANCE, ADD_ADVANCE_DAY, ADD_EXTRA_INCOME = range(6, 12)

async def manage_income_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начинает диалог управления доходами."""
    keyboard = ReplyKeyboardMarkup([
        ["Основной доход"],
        ["Дополнительный доход"],
        ["Просмотреть доходы"],
        ["Удалить доходы"],
        ["Назад"]
    ], resize_keyboard=True)
    await update.message.reply_text("Выберите тип дохода:", reply_markup=keyboard)
    return INCOME_MENU

async def handle_income_menu(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает выбор в меню доходов."""
    choice = update.message.text
    
    if choice == "Основной доход":
        await update.message.reply_text("Введите размер основной части зарплаты:")
        return ADD_MAIN_INCOME
    
    elif choice == "Дополнительный доход":
        await update.message.reply_text("Введите размер дополнительного дохода:")
        return ADD_EXTRA_INCOME
    
    elif choice == "Просмотреть доходы":
        user_data = storage.get_user_data(str(update.effective_user.id))
        income_data = user_data.get('income', {})
        
        if not income_data:
            await update.message.reply_text("У вас пока нет сохраненных доходов")
        else:
            result = "📋 Ваши доходы:\n\n"
            if 'main_salary' in income_data:
                result += f"💰 Основная зарплата: {income_data['main_salary']:,.2f} руб.\n"
                result += f"📅 День выплаты: {income_data.get('main_salary_day', 'не указан')}\n\n"
            if 'advance' in income_data:
                result += f"💰 Аванс: {income_data['advance']:,.2f} руб.\n"
                result += f"📅 День выплаты: {income_data.get('advance_day', 'не указан')}\n\n"
            if 'extra' in income_data:
                result += f"💰 Дополнительный доход: {income_data['extra']:,.2f} руб.\n"
            
            await update.message.reply_text(result)
        return INCOME_MENU
    
    elif choice == "Удалить доходы":
        user_data = storage.get_user_data(str(update.effective_user.id))
        if 'income' in user_data:
            del user_data['income']
            storage.update_user_data(str(update.effective_user.id), user_data)
            await update.message.reply_text("Все данные о доходах удалены")
        else:
            await update.message.reply_text("Нет сохраненных данных о доходах")
        return INCOME_MENU
    elif choice == "Назад":
        await update.message.reply_text("Возвращаемся в главное меню")
        return ConversationHandler.END
    else:
        await update.message.reply_text("Пожалуйста, выберите действие из меню")
        return INCOME_MENU

async def add_main_income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получает размер основной зарплаты."""
    try:
        amount = float(update.message.text)
        context.user_data['temp_income'] = {'main_salary': amount}
        await update.message.reply_text("Введите день выплаты основной зарплаты (1-31):")
        return ADD_MAIN_INCOME_DAY
    except ValueError:
        await update.message.reply_text("Некорректная сумма. Пожалуйста, введите число:")
        return ADD_MAIN_INCOME

async def add_main_income_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получает день выплаты основной зарплаты."""
    try:
        day = int(update.message.text)
        if 1 <= day <= 31:
            context.user_data['temp_income']['main_salary_day'] = day
            await update.message.reply_text("Введите размер аванса (если нет, введите 0):")
            return ADD_ADVANCE
        await update.message.reply_text("Введите число от 1 до 31:")
        return ADD_MAIN_INCOME_DAY
    except ValueError:
        await update.message.reply_text("Некорректный день. Введите число от 1 до 31:")
        return ADD_MAIN_INCOME_DAY

async def add_advance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получает размер аванса."""
    try:
        amount = float(update.message.text)
        context.user_data['temp_income']['advance'] = amount
        if amount > 0:
            await update.message.reply_text("Введите день выплаты аванса (1-31):")
            return ADD_ADVANCE_DAY
        else:
            await save_income(update, context)
            return ConversationHandler.END
    except ValueError:
        await update.message.reply_text("Некорректная сумма. Пожалуйста, введите число:")
        return ADD_ADVANCE

async def add_advance_day(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получает день выплаты аванса."""
    try:
        day = int(update.message.text)
        if 1 <= day <= 31:
            context.user_data['temp_income']['advance_day'] = day
            await save_income(update, context)
            return ConversationHandler.END
        await update.message.reply_text("Введите число от 1 до 31:")
        return ADD_ADVANCE_DAY
    except ValueError:
        await update.message.reply_text("Некорректный день. Введите число от 1 до 31:")
        return ADD_ADVANCE_DAY

async def add_extra_income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Получает дополнительный доход."""
    try:
        amount = float(update.message.text)
        user_data = storage.get_user_data(str(update.effective_user.id))
        if 'income' not in user_data:
            user_data['income'] = {}
        user_data['income']['extra'] = amount
        storage.update_user_data(str(update.effective_user.id), user_data)
        await update.message.reply_text(f"Дополнительный доход {amount:,.2f} руб. успешно сохранен")
        return INCOME_MENU
    except ValueError:
        await update.message.reply_text("Некорректная сумма. Пожалуйста, введите число:")
        return ADD_EXTRA_INCOME

async def save_income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняет данные о доходах."""
    temp_income = context.user_data.get('temp_income', {})
    user_data = storage.get_user_data(str(update.effective_user.id))

    if 'income' not in user_data:
        user_data['income'] = {}

    user_data['income'].update({
        'main_salary': temp_income.get('main_salary', 0),
        'main_salary_day': temp_income.get('main_salary_day', 1),
        'advance': temp_income.get('advance', 0),
        'advance_day': temp_income.get('advance_day', 15) if temp_income.get('advance', 0) > 0 else None
    })

    storage.update_user_data(str(update.effective_user.id), user_data)
    await update.message.reply_text("Данные о доходах успешно сохранены!")
    return ConversationHandler.END

async def view_income(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Отображает информацию о доходах."""
    user_data = storage.get_user_data(str(update.effective_user.id))
    income_data = user_data.get('income', {})

    if not income_data:
        await update.message.reply_text("У вас пока не добавлено информации о доходах.")
        return

    result = "📊 Информация о доходах:\n\n"

    if 'main_salary' in income_data:
        result += (
            f"💰 Основная зарплата: {income_data['main_salary']:,.2f} руб.\n"
            f"📅 День выплаты: {income_data['main_salary_day']}\n"
        )

    if income_data.get('advance', 0) > 0:
        result += (
            f"\n💵 Аванс: {income_data['advance']:,.2f} руб.\n"
            f"📅 День выплаты: {income_data['advance_day']}\n"
        )

    if 'extra' in income_data:
        result += f"\n✨ Дополнительный доход: {income_data['extra']:,.2f} руб.\n"

    total = (
        income_data.get('main_salary', 0) +
        income_data.get('advance', 0) +
        income_data.get('extra', 0)
    )
    result += f"\n💎 Общий месячный доход: {total:,.2f} руб."

    await update.message.reply_text(result)
async def get_summary(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Предоставляет сводную информацию по доходам, расходам и кредитам."""
    user_data = storage.get_user_data(str(update.effective_user.id))
    current_date = datetime.date.today()
    next_month = current_date.replace(day=1) + datetime.timedelta(days=32)
    next_month = next_month.replace(day=1)

    # Получаем информацию о доходах
    income_data = user_data.get('income', {})
    main_salary = income_data.get('main_salary', 0)
    main_salary_day = income_data.get('main_salary_day')
    advance = income_data.get('advance', 0)
    advance_day = income_data.get('advance_day')
    extra_income = income_data.get('extra', 0)
    total_income = main_salary + advance + extra_income

    # Получаем информацию о регулярных расходах
    regular_expenses = user_data.get('regular_expenses', [])
    total_regular_expenses = sum(expense['amount'] for expense in regular_expenses)

    # Получаем информацию о кредитах
    loans = user_data.get('loans', [])
    total_monthly_credit_payments = 0
    credit_info = ""
    for loan in loans:
        monthly_rate = loan['rate'] / 100 / 12
        monthly_payment = (loan['amount'] * monthly_rate) / (1 - (1 + monthly_rate) ** -loan['term'])
        total_monthly_credit_payments += monthly_payment
        credit_info += f"- {loan['name']}: {monthly_payment:,.2f} руб. ({loan['payment_day']} числа)\n"

    # Формируем сводку
    summary = "📊 Сводная информация\n\n"
    
    # Текущий месяц
    summary += f"🗓 ТЕКУЩИЙ МЕСЯЦ ({current_date.strftime('%B %Y')})\n"
    summary += f"💰 Общий доход: {total_income:,.2f} руб.\n"
    if main_salary:
        summary += f"- Основная зарплата: {main_salary:,.2f} руб. ({main_salary_day} числа)\n"
    if advance:
        summary += f"- Аванс: {advance:,.2f} руб. ({advance_day} числа)\n"
    if extra_income:
        summary += f"- Дополнительный доход: {extra_income:,.2f} руб.\n"
    
    summary += f"\n📝 Регулярные расходы: {total_regular_expenses:,.2f} руб.\n"
    for expense in regular_expenses:
        summary += f"- {expense['name']}: {expense['amount']:,.2f} руб. ({expense['day']} числа)\n"

    if loans:
        summary += f"\n💳 Кредитные платежи: {total_monthly_credit_payments:,.2f} руб.\n"
        summary += credit_info
    
    total_expenses = total_regular_expenses + total_monthly_credit_payments
    balance = total_income - total_expenses
    summary += f"\n💵 Остаток: {balance:,.2f} руб.\n"

    # Расчет остатка на день до следующего дохода
    if main_salary_day or advance_day:
        next_income_date = None
        next_income_amount = 0
        
        # Определяем следующую дату дохода
        if main_salary_day:
            main_salary_date = current_date.replace(day=main_salary_day)
            if main_salary_date <= current_date:
                main_salary_date = main_salary_date.replace(
                    month=main_salary_date.month + 1 if main_salary_date.month < 12 else 1,
                    year=main_salary_date.year + (1 if main_salary_date.month == 12 else 0)
                )
            if not next_income_date or main_salary_date < next_income_date:
                next_income_date = main_salary_date
                next_income_amount = main_salary

        if advance_day:
            advance_date = current_date.replace(day=advance_day)
            if advance_date <= current_date:
                advance_date = advance_date.replace(
                    month=advance_date.month + 1 if advance_date.month < 12 else 1,
                    year=advance_date.year + (1 if advance_date.month == 12 else 0)
                )
            if not next_income_date or advance_date < next_income_date:
                next_income_date = advance_date
                next_income_amount = advance

        if next_income_date:
            days_until_income = (next_income_date - current_date).days
            daily_balance = balance / days_until_income if days_until_income > 0 else 0
            summary += f"\n💰 Остаток на день до {next_income_date.strftime('%d.%m.%Y')}: {daily_balance:,.2f} руб.\n"

    # Следующий месяц
    summary += f"\n🗓 СЛЕДУЮЩИЙ МЕСЯЦ ({next_month.strftime('%B %Y')})\n"
    summary += f"💰 Ожидаемый доход: {total_income:,.2f} руб.\n"
    summary += f"📝 Ожидаемые регулярные расходы: {total_regular_expenses:,.2f} руб.\n"
    if loans:
        summary += f"💳 Кредитные платежи: {total_monthly_credit_payments:,.2f} руб.\n"
    summary += f"💵 Ожидаемый остаток: {balance:,.2f} руб.\n"

    await update.message.reply_text(summary)
