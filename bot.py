from handlers.forecast.actions import (
    calculate_daily_balance_start,
    ask_balance,
    ask_salary_day,
    daily_balance_handler,
)

from storage import Storage

# Initialize storage
storage = Storage()