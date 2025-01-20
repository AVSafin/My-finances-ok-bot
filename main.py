import logging
import os
import asyncio  # Импортируем asyncio

from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, CallbackContext, filters

# Включаем логирование для отслеживания ошибок
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO)


# Асинхронная функция для обработки команды /start
async def start(update: Update, context: CallbackContext):
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text="Привет! Я твой бот.")


# Асинхронная функция для обработки текстовых сообщений
async def echo(update: Update, context: CallbackContext):
    await context.bot.send_message(chat_id=update.effective_chat.id,
                                   text=update.message.text)


# Асинхронная функция для отправки сообщения каждые 5 минут
async def send_periodic_message(context: CallbackContext):
    while True:
        await asyncio.sleep(300)  # Пауза в 5 минут (300 секунд)
        await context.bot.send_message(
            chat_id=371421224,
            text="Это сообщение отправляется каждые 5 минут!")


async def main():
    # Получаем токен бота из Replit Secrets
    TOKEN = os.environ['TOKEN']

    # Создаем объект Application, передавая токен
    application = Application.builder().token(TOKEN).build()

    # Добавляем обработчик для команды /start
    application.add_handler(CommandHandler('start', start))

    # Добавляем обработчик для всех текстовых сообщений
    application.add_handler(
        MessageHandler(filters.TEXT & (~filters.COMMAND), echo))

    # Запускаем периодическую отправку сообщений
    application.job_queue.run_once(send_periodic_message, 0, context=None)

    # Запускаем бота
    await application.run_polling()


if __name__ == '__main__':
    asyncio.run(main())
