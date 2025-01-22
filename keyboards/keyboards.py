from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup

main_keyboard = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("Кредиты", callback_data="credits")],
        [InlineKeyboardButton("Сбережения", callback_data="savings")],
        [InlineKeyboardButton("Прогнозирование", callback_data="forecast")],
    ]
)

loan_keyboard = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("Назад", callback_data="back_to_main")],
    ]
)

show_keyboard = InlineKeyboardMarkup(
    [
        [
            InlineKeyboardButton("Главное меню", callback_data="start"),
        ]
    ]
)

def bank_keyboard(banks):
    keyboard = []
    for bank in banks:
      keyboard.append([InlineKeyboardButton(text=bank, callback_data=f"bank_{bank}")])
    keyboard.append([InlineKeyboardButton("Назад", callback_data="back_to_main")])
    return InlineKeyboardMarkup(keyboard)

def purpose_keyboard(purposes):
    keyboard = []
    for purpose in purposes:
      keyboard.append([InlineKeyboardButton(text=purpose, callback_data=f"purpose_{purpose}")])
    keyboard.append([InlineKeyboardButton("Назад", callback_data="back_to_main")])
    return InlineKeyboardMarkup(keyboard)

credits_menu_keyboard = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("Добавить кредит", callback_data="calculate_loan"), InlineKeyboardButton("Удалить кредит", callback_data="delete_loans")],
        [InlineKeyboardButton("Просмотреть кредиты", callback_data="show_loans")],
        [InlineKeyboardButton("Изменить дату платежа", callback_data="change_date")],
        [InlineKeyboardButton("Назад", callback_data="back_to_main")]
    ]
)