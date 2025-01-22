from datetime import datetime, timedelta

def calculate_annuity_payment(loan_amount: float, interest_rate: float, loan_term: int) -> float:
    """Calculate the monthly annuity payment."""
    monthly_interest_rate = interest_rate / 100 / 12
    payment = (
        loan_amount
        * monthly_interest_rate
        * (1 + monthly_interest_rate) ** loan_term
    ) / ((1 + monthly_interest_rate) ** loan_term - 1)
    return round(payment, 2)

def calculate_payments_schedule(loan_amount, interest_rate, loan_term, start_date):
    """Generate the payments schedule."""
    monthly_payment = calculate_annuity_payment(loan_amount, interest_rate, loan_term)
    schedule = []
    remaining_balance = loan_amount
    monthly_interest_rate = interest_rate / 100 / 12
    current_date = start_date

    for _ in range(loan_term):
        interest_payment = remaining_balance * monthly_interest_rate
        principal_payment = monthly_payment - interest_payment
        remaining_balance -= principal_payment
        schedule.append({
            "date": current_date.strftime("%Y-%m-%d"),
            "principal": round(principal_payment, 2),
            "interest": round(interest_payment, 2),
            "payment": round(monthly_payment, 2),
        })
        current_date += timedelta(days=30)  # Roughly 1 month
    return schedule