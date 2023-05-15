from aiogram import types, Dispatcher
from tgbot.create_bot import dp

#@dp.message_handler(commands=['start'])
async def get_started(message: types.Message):
    await message.answer('Вас приветствует Бот Мосгортранс!\n'
                         '/form - заполнить заявку на поиск вещи')
    await message.delete()

#@dp.message_handler(commands=['help'])
async def get_help(message: types.Message):
    await message.answer('Упс. Тут пока пусто')

def register_handlers_star_help(dp: Dispatcher):
    dp.register_message_handler(get_started, commands=['start'])
    dp.register_message_handler(get_help, commands=['help'])
    