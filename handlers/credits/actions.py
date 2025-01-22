from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import ContextTypes, ConversationHandler

# Этапы диалога
ASK_BANK, ASK_CATEGORY, ASK_AMOUNT, ASK_RATE, ASK_TERM, ASK_DAY, ASK_DATE = range(7)

CREDITS_MENU = [["Добавить кредит", "Просмотреть кредиты"], ["График платежей", "Удалить кредит"], ["Назад"]]
BANKS = [["Сбербанк", "Альфа-Банк"], ["Тинькофф", "ВТБ"], ["Газпромбанк", "Райффайзенбанк"], ["Назад"]]
CATEGORIES = [["Ипотека", "Автокредит"], ["Кредит наличными", "Кредитная карта"], ["Назад"]]

async def start_add_credit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Начало процесса добавления кредита."""
    keyboard = ReplyKeyboardMarkup(BANKS, resize_keyboard=True)
    await update.message.reply_text("Выберите банк из списка:", reply_markup=keyboard)
    return ASK_BANK

async def ask_bank(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняет выбор банка и предлагает выбрать категорию кредита."""
    context.user_data["bank"] = update.message.text
    keyboard = ReplyKeyboardMarkup(CATEGORIES, resize_keyboard=True)
    await update.message.reply_text("Выберите категорию кредита:", reply_markup=keyboard)
    return ASK_CATEGORY

async def ask_category(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Сохраняет выбор категории и спрашивает сумму кредита."""
    context.user_data["category"] = update.message.text
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
    context.user_data["date"] = update.message.text
    # Составляем название кредита
    credit_name = f"{context.user_data['bank']} | {context.user_data['payment_day']} число | {context.user_data['amount']} руб."

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
        f"Кредит успешно добавлен:\n"
        f"Название: {credit['name']}\n"
        f"Банк: {credit['bank']}\n"
        f"Категория: {credit['category']}\n"
        f"Сумма: {credit['amount']} руб.\n"
        f"Ставка: {credit['rate']}%\n"
        f"Срок: {credit['term']} месяцев\n"
        f"День платежа: {credit['payment_day']}\n"
        f"Дата первого платежа: {credit['date']}",
        reply_markup=ReplyKeyboardMarkup(CREDITS_MENU, resize_keyboard=True),
    )
    return ConversationHandler.END