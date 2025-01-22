from datetime import datetime, timedelta
import calendar

def calculate_annuity_payment(loan_amount: float, interest_rate: float, loan_term: int) -> float:
    """Рассчитывает ежемесячный аннуитетный платеж."""
    monthly_interest_rate = interest_rate / 100 / 12
    payment = (
        loan_amount
        * monthly_interest_rate
        * (1 + monthly_interest_rate) ** loan_term
    ) / ((1 + monthly_interest_rate) ** loan_term - 1)
    return payment

def calculate_payments_schedule(loan_amount: float, annual_interest_rate: float, loan_term: int, start_day: int) -> list:
    """Вычисляет график платежей."""
    monthly_interest_rate = annual_interest_rate / 100 / 12
    monthly_payment = calculate_annuity_payment(loan_amount, annual_interest_rate, loan_term)

    schedule = []
    current_date = datetime.now().replace(day=start_day)
    if current_date.day != start_day:
        if current_date.day > start_day:
            current_date = current_date.replace(month = current_date.month + 1)
        current_date = current_date.replace(day = start_day)

    remaining_balance = loan_amount
    for month in range(loan_term):
        interest_payment = remaining_balance * monthly_interest_rate
        principal_payment = monthly_payment - interest_payment

        if remaining_balance < principal_payment:
            principal_payment = remaining_balance
            monthly_payment = principal_payment + interest_payment

        remaining_balance -= principal_payment

        if current_date.month == 12:
            current_date = current_date.replace(year = current_date.year + 1, month = 1)
        else:
             current_date = current_date.replace(month = current_date.month + 1)

        schedule.append({
            'date': current_date.strftime("%Y-%m-%d"),
            'principal': principal_payment,
            'interest': interest_payment,
            'payment': monthly_payment
        })
    return schedule
