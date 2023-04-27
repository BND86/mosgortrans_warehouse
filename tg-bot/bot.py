import logging
from aiogram import executor
from tgbot.create_bot import dp
from handlers import fill_form, start_help


logging.basicConfig(level=logging.INFO)

fill_form.register_handlers_fill_form(dp)
start_help.register_handlers_fill_form(dp)

if __name__ == '__main__':
    # Запускаем бота
    executor.start_polling(dp, skip_updates=True)
