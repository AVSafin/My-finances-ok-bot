
from telegram import Update, ReplyKeyboardMarkup
from telegram.ext import CallbackContext

from keyboards import main_menu_keyboard
from handlers import credits_handler

async def handle_main_menu(update: Update, context: CallbackContext) -> None:
    text = update.message.text
    if text == "Кредиты":
        await credits_handler.handle_credits_menu(update, context)
    elif text == "Сбережения":
        await update.message.reply_text("Раздел 'Сбережения' пока в разработке.")
    elif text == "Прогнозирование":
        await update.message.reply_text("Раздел 'Прогнозирование' пока в разработке.")
    else:
        await update.message.reply_text("Пожалуйста, выберите один из разделов: Кредиты, Сбережения или Прогнозирование.",
                                         reply_markup=ReplyKeyboardMarkup(main_menu_keyboard, resize_keyboard=True))
