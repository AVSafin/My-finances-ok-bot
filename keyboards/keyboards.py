from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_menu_keyboard = ReplyKeyboardMarkup(resize_keyboard=True)
main_menu_keyboard.add(KeyboardButton("Кредиты"))
main_menu_keyboard.add(KeyboardButton("Сбережения"))
main_menu_keyboard.add(KeyboardButton("Прогнозирование"))

credits_menu_keyboard = [["Добавить кредит", "Удалить кредит"], ["Просмотреть кредиты"], ["Изменить дату платежа"], ["Назад"]]

__all__ = ["main_menu_keyboard", "credits_menu_keyboard"]
