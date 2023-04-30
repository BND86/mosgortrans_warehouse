import re
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext, filters
from aiogram import types, Dispatcher
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from tgbot.create_bot import dp


class Form(StatesGroup):
    phone = State()
    name = State()      # Состояние для запроса имени
    surname = State()   # Состояние для запроса фамилии
    patronymic = State() # Состояние для запроса отчества
    email = State() # Состояние для запроса почты
    description = State() # Состояние для запроса описания
    photo = State()

# Проверка валидности почты
regex = re.compile(r'([A-Za-z0-9]+[.-_])*[A-Za-z0-9]+@[A-Za-z0-9-]+(\.[A-Z|a-z]{2,})+')
def isValid(email):
    if re.fullmatch(regex, email):
        return True
    return False

regexfio = re.compile(r'[А-ЯЁ]{1}[а-яё]+')
def ValidFio(fio):
    if re.fullmatch(regexfio, fio):
        return True
    return False

# Начинаем заполнение формы
async def insert_form_phone_1(message: types.Message, state: FSMContext):
    # Создаем временную кнопку для отправки номера
    kb = ReplyKeyboardMarkup(resize_keyboard=True)
    kb.add(KeyboardButton(text="Отправить номер", request_contact=True))
    await message.answer(text='Отправьте мне свой номер',
                         reply_markup=kb)
    await message.delete()
    await state.set_state(Form.phone)

async def insert_form_phone_2(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['phone'] = message.contact['phone_number']
    # Удаляем временную кнопку
    await message.answer('Номер принят', reply_markup=ReplyKeyboardRemove())
    await message.answer('Введите ваше имя')
    # Переходим в состояние "name"
    await Form.name.set()

async def process_name(message: types.Message, state: FSMContext):
    # Сохраняем имя в контексте
    async with state.proxy() as data:
        data['name'] = message.text
    # Запрашиваем фамилию
    await message.answer("Введите вашу фамилию")
    # Переходим в состояние "surname"
    await Form.surname.set()

async def process_surname(message: types.Message, state: FSMContext):
    #Сохраняем фамилию в контексте
    async with state.proxy() as data:
        data['surname'] = message.text
    # Запрашиваем отчество
    await message.answer("Введите ваше отчество")
    # Переходим в состояние "patronymic"
    await Form.patronymic.set()

async def process_patronymic(message: types.Message, state: FSMContext):
    # Сохраняем отчество в контексте
    async with state.proxy() as data:
        data['patronymic'] = message.text
    # Завершаем состояние
    await Form.email.set()
    await message.answer('Введите ваш адрес электронной почты')

async def insert_form_email(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['email'] = message.text
    await Form.description.set()
    await message.answer('Добавьте краткое описание утерянной вещи')

async def insert_form_description(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['description'] = message.text
        await message.answer('Ваша заявка сформирована.\n''ПОЖАЛУЙСТА, ПРОВЕРЬТЕ ПРАВИЛЬНОСТЬ ДАННЫХ!\n'
                             'При необходимости выберите данные для изменения.\n'
                             'Если данные верны - нажмите кнопку "Отправить заявку"\n\n'
                             f"ФИО: {data['surname']} {data['name']} {data['patronymic']}\n\n"
                             f"Электронная почта: {data['email']}\n\n"
                             f"Телефон: {data['phone']}\n\n"
                             f"Утерянная вещь:\n{data['description']}")
    user_data = await state.get_data()
    print(user_data)
    await state.finish()
    #await message.answer('Вы также можете отправить фото')
    #await Form.photo.set()

#--------------------------------------------------------------
# ЧАСТИТЧНО РАБОТАЕТ

#@dp.message_handler(state=Form.photo)
# async def process_photo(message: types.Message, state: FSMContext):
#     photo = message.photo[-1]
#     photo_file = await photo.download(destination='media')
#     await message.answer_photo(photo=open(photo_file, 'rb'))
#     await state.finish()

#---------------------------------------------------------------


def register_handlers_fill_form(dp: Dispatcher):
    dp.register_message_handler(insert_form_phone_1, commands=['form'])
    dp.register_message_handler(insert_form_phone_2, filters.IsSenderContact(True), content_types='contact', state = Form.phone)
    dp.register_message_handler(process_name, lambda msg: ValidFio(msg.text) == True, state=Form.name)
    dp.register_message_handler(process_surname, lambda msg: ValidFio(msg.text) == True, state=Form.surname)
    dp.register_message_handler(process_patronymic, lambda msg: ValidFio(msg.text) == True, state=Form.patronymic)
    dp.register_message_handler(insert_form_email, lambda msg: isValid(msg.text) == True, state=Form.email)
    dp.register_message_handler(insert_form_description, state=Form.description)
    #dp.register_message_handler(process_photo, state=Form.photo)