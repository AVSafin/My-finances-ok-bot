from telegram import InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup

main_keyboard = InlineKeyboardMarkup(
    [
        [InlineKeyboardButton("Рассчитать кредит", callback_data="calculate_loan")],
        [InlineKeyboardButton("Посмотреть данные", callback_data="show_loans"), InlineKeyboardButton("Удалить кредит", callback_data="delete_loans")],
        [InlineKeyboardButton("Сбережения", callback_data="savings"), InlineKeyboardButton("Прогнозирование", callback_data="forecast")],
    ]
    )

main_menu_keyboard =  [
        ["Кредиты"],
        ["Сбережения"],
        ["Прогнозирование"]
    ]


loan_keyboard = ReplyKeyboardMarkup(
    [
        ["Назад"],
    ],
    resize_keyboard=True
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

credits_menu_keyboard = ReplyKeyboardMarkup(
    [
        ["Добавить кредит", "Удалить кредит"],
        ["Просмотреть кредиты"],
        ["Изменить дату платежа"],
        ["Назад"]
    ],
    resize_keyboard=True
)