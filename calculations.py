from datetime import date
from dateutil.relativedelta import relativedelta

def calculate_annuity_payment(loan_amount, interest_rate, loan_term_months):
    """Рассчитывает ежемесячный аннуитетный платеж."""
    monthly_rate = interest_rate / 12 / 100
    annuity_payment = loan_amount * (
        (monthly_rate * (1 + monthly_rate) ** loan_term_months)
        / ((1 + monthly_rate) ** loan_term_months - 1)
    )
    return round(annuity_payment, 2)

def calculate_payments_schedule(loan_amount, interest_rate, loan_term_months, payment_date_day):
    """Рассчитывает график платежей по кредиту."""
    monthly_rate = interest_rate / 12 / 100
    annuity_payment = calculate_annuity_payment(loan_amount, interest_rate, loan_term_months)
    schedule = []
    remaining_balance = loan_amount
    today = date.today()
    first_payment_date = date(today.year, today.month, payment_date_day)

    if first_payment_date < today:
       first_payment_date = first_payment_date + relativedelta(months=1)

    payment_date = first_payment_date

    for _ in range(loan_term_months):
        interest_payment = remaining_balance * monthly_rate
        principal_payment = annuity_payment - interest_payment
        remaining_balance -= principal_payment
        schedule.append({
            "date": payment_date.strftime("%Y-%m-%d"),
            "principal": round(principal_payment, 2),
            "interest": round(interest_payment, 2),
            "payment": annuity_payment
        })
        payment_date += relativedelta(months=1)

    return schedule