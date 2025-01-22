import logging
from telegram import Update
from telegram.ext import ContextTypes

async def handle_error(update: Update, context: ContextTypes.DEFAULT_TYPE):
    logging.exception(f"Ошибка в обработке обновления: {update}")
