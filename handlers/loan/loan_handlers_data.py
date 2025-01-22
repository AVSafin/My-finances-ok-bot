
from datetime import datetime

def format_loan_name(bank_name, payment_date, balance):
    return f"{bank_name} | {payment_date} | Остаток: {balance}₽"

def update_payment_date(loans, loan_id, new_date):
    if loan_id in loans:
        try:
            loans[loan_id]['payment_date'] = new_date
            return True, f"Дата платежа успешно обновлена на {new_date}."
        except Exception as e:
            return False, f"Ошибка при обновлении даты: {e}"
    else:
        return False, "Кредит с указанным ID не найден."

top_banks = [
    "Сбербанк",
    "Тинькофф",
    "Альфа-Банк",
    "ВТБ",
    "Газпромбанк",
    "Открытие"
]

top_purposes = [
    "Покупка квартиры",
    "Покупка машины",
    "Ремонт",
    "Образование",
    "Отдых",
    "Другое"
]