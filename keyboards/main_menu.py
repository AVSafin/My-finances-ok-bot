from telegram import InlineKeyboardMarkup, InlineKeyboardButton

def get_main_menu_keyboard():
    """Создает клавиатуру главного меню."""
    keyboard = [
        [InlineKeyboardButton("Кредиты", callback_data="credits")],
        [InlineKeyboardButton("Сбережения", callback_data="savings")],
        [InlineKeyboardButton("Прогнозирование", callback_data="forecast")],
    ]
    return InlineKeyboardMarkup(keyboard)