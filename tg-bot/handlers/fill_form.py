import re
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.dispatcher import FSMContext, filters
from aiogram import types, Dispatcher
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove, CallbackQuery
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from tgbot.create_bot import bot
from pg_connect import connection, write_photo
import psycopg2
from datetime import datetime, date


class Form(StatesGroup):
    phone = State()
    name = State()      # Состояние для запроса имени
    surname = State()   # Состояние для запроса фамилии
    patronymic = State() # Состояние для запроса отчества
    email = State() # Состояние для запроса почты
    short_desc = State()
    date = State()
    bus = State()
    description = State() # Состояние для запроса описания
    result = State()
    send_to_db = State()

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

regexdate = re.compile(r'(0[1-9]|[12][0-9]|3[01])[- /.](0[1-9]|1[012])[- /.](19|20)\d\d')
curr_date = date.today()
def Valid_date(info):
    try:
        info_date = datetime.strptime(info, '%d-%m-%Y').date()
    except ValueError:
        try:
            info_date = datetime.strptime(info, '%d/%m/%Y').date()
        except ValueError:
            try:
                info_date = datetime.strptime(info, '%d.%m.%Y').date()
            except ValueError:
                try:
                    info_date = datetime.strptime(info, '%d %m %Y').date()
                except ValueError:
                    return False
    if re.fullmatch(regexdate, info) and info_date <= curr_date:
        return True
    return False

photo_path = ''
photo_flag = False

kb_cancel = InlineKeyboardMarkup()
cancel_button = InlineKeyboardButton(text='Отмена❌', callback_data='cancel')
kb_cancel.add(cancel_button)

async def cancel_handler(callback: CallbackQuery, state: FSMContext):
    await state.finish() # очищаем все состояния
    await callback.message.answer(text='Отменено') # отправляем ответ пользователю
    await callback.message.delete_reply_markup() # удаляем клавиатуру

async def nopatr_handler(callback: CallbackQuery, state: FSMContext):
    async with state.proxy() as data:
            data['patronymic'] = '-'
    await Form.email.set()
    await callback.message.delete_reply_markup() # удаляем клавиатуру
    await callback.message.delete()
    await callback.message.answer('Введите ваш адрес электронной почты', reply_markup = kb_cancel)




# Начинаем заполнение формы
async def insert_form_phone_1(message: types.Message, state: FSMContext):
    kb = ReplyKeyboardMarkup()
    kb.add(KeyboardButton(text="Отправить номер", request_contact=True))
    await message.answer(text='Начинаем заполнение заявки на поиск потерянной вещи', reply_markup = kb)
    await message.answer(text='Отправьте мне свой номер', reply_markup = kb_cancel)
    await message.delete()
    await state.set_state(Form.phone)

async def insert_form_phone_2(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['phone'] = message.contact['phone_number']
    await message.answer('Номер принят', reply_markup=ReplyKeyboardRemove())
    await message.answer('Введите ваше имя', reply_markup = kb_cancel)
    await Form.name.set()

async def process_name(message: types.Message, state: FSMContext):
    if ValidFio(message.text) == True:
        async with state.proxy() as data:
            data['name'] = message.text
        await message.answer("Введите вашу фамилию", reply_markup = kb_cancel)
        await Form.surname.set()
    else:
        await message.answer("Вы ввели некоректное имя")

async def process_surname(message: types.Message, state: FSMContext):
    if ValidFio(message.text) == True:
        async with state.proxy() as data:
            data['surname'] = message.text
        kb_cancel_nopatr = InlineKeyboardMarkup()
        nopatr_button = InlineKeyboardButton(text='Без отчества', callback_data='nopatr')
        kb_cancel_nopatr.add(cancel_button)
        kb_cancel_nopatr.add(nopatr_button)
        await message.answer("Введите ваше отчество", reply_markup = kb_cancel_nopatr)
        await Form.patronymic.set()
    else:
        await message.answer("Вы ввели некоректную фамилию")

async def process_patronymic(message: types.Message, state: FSMContext):
    if ValidFio(message.text) == True:
        async with state.proxy() as data:
            data['patronymic'] = message.text
        await message.answer('Введите ваш адрес электронной почты', reply_markup = kb_cancel)
        await Form.email.set()
    else:
        await message.answer("Вы ввели некоректное отчество")

async def insert_form_email(message: types.Message, state: FSMContext):
    if isValid(message.text) == True:
        async with state.proxy() as data:
            data['email'] = message.text
        await Form.date.set()
        await message.answer('Укажите дату утери в формате ДД-ММ-ГГГГ', reply_markup = kb_cancel)
    else:
        await message.answer("Вы ввели некоректный адрес электронной почты")

async def insert_form_date(message: types.Message, state: FSMContext):
    if Valid_date(message.text) == True:
        async with state.proxy() as data:
            data['date'] = message.text
        await Form.bus.set()
        await message.answer('Введите номер автобуса, в котором была забыта вещь', reply_markup = kb_cancel)
    else:
        await message.answer("Вы ввели некорекную дату")

async def insert_form_bus_number(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['bus'] = message.text
    await Form.short_desc.set()
    await message.answer('Введите название утерянной вещи', reply_markup = kb_cancel)

async def insert_form_short_desc(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['lost_thing'] = message.text
    await message.answer('Добавьте описание утерянной вещи', reply_markup = kb_cancel)
    await Form.description.set()

async def insert_form_description(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['description'] = message.text
    no_photo = ReplyKeyboardMarkup()
    no_photo.add(KeyboardButton(text="Без фотографии"))
    await message.answer('Вы также можете отправить фотографию', reply_markup = no_photo)
    await Form.result.set()

async def result(message: types.Message, state: FSMContext):
    global photo_path, photo_flag
    async with state.proxy() as data:
        await message.answer('Ваша заявка сформирована.\n'
                            f"ФИО: {data['surname']} {data['name']} {data['patronymic']}\n\n"
                            f"Электронная почта: {data['email']}\n\n"
                            f"Телефон: {data['phone']}\n\n"
                            f"Дата утери: {data['date']}\n\n"
                            f"Номер автобуса: {data['bus']}\n\n"
                            f"Утерянная вещь:\n{data['lost_thing']}\n{data['description']}\n\n"
                            'ПОЖАЛУЙСТА, ПРОВЕРЬТЕ ПРАВИЛЬНОСТЬ ДАННЫХ!\n'
                            'При необходимости заполните форму повторно.\n', reply_markup=ReplyKeyboardRemove())
    if message.photo:
        await message.photo[-1].download(destination_dir="tgbot")
        await message.answer_photo(message.photo[-1].file_id)
        file_info = await bot.get_file(message.photo[-1].file_id)
        print(file_info)
        photo_path = 'C:/Programming/Warehouse/mosgortrans_warehouse/tg-bot/tgbot/' + file_info.file_path
        photo_flag = True
    send_form = InlineKeyboardMarkup()
    send_form.add(InlineKeyboardButton(text="Отправить заявку", callback_data="Отправить заявку"))
    send_form.add(InlineKeyboardButton(text="Удалить заявку", callback_data='cancel'))
    await message.answer('Если данные верны - нажмите кнопку "Отправить заявку"', reply_markup=send_form)
    await Form.send_to_db.set()

async def data_db(callback: CallbackQuery, state: FSMContext):
    global photo_path, photo_flag
    user_data = await state.get_data()
    print(user_data)
    await state.finish()
    try:
        conn = connection
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute(f"""INSERT INTO requests(item_description, comment_, date_time_of_loss, bus_route, email, phone, name_, fam, surname)
        VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s);""",
        [user_data['lost_thing'],
        user_data['description'],
        user_data['date'],
        user_data['bus'],
        user_data['email'],
        user_data['phone'],
        user_data['name'],
        user_data['surname'],
        user_data['patronymic']])
        connection.commit()
        if photo_flag:
            cur.execute("SELECT max(individual_number) FROM requests;")
            write_photo(cur.fetchone(), photo_path)

    except psycopg2.InterfaceError as exc:
        print(exc)
        conn = connection
        conn.autocommit = True
        cur = conn.cursor()
    except Exception as _ex:
        print("[INFO] Error while working with PostgreSQL", _ex)

    await callback.message.answer('Оправлено)', reply_markup=ReplyKeyboardRemove())

def register_handlers_fill_form(dp: Dispatcher):
    dp.register_message_handler(insert_form_phone_1, commands=['form'])
    dp.register_message_handler(insert_form_phone_2, filters.IsSenderContact(True), content_types='contact', state = Form.phone)
    dp.register_message_handler(process_name, state=Form.name)
    dp.register_message_handler(process_surname, state=Form.surname)
    dp.register_message_handler(process_patronymic, state=Form.patronymic)
    dp.register_message_handler(insert_form_email, state=Form.email)
    dp.register_message_handler(insert_form_date, state=Form.date)
    dp.register_message_handler(insert_form_bus_number, state=Form.bus)
    dp.register_message_handler(insert_form_short_desc, state=Form.short_desc)
    dp.register_message_handler(insert_form_description, state=Form.description)
    dp.register_callback_query_handler(data_db, text = 'Отправить заявку', state=Form.send_to_db)
    dp.register_message_handler(result, content_types=['photo', 'text'], state=Form.result)
    dp.register_callback_query_handler(cancel_handler, text = 'cancel', state='*')
    dp.register_callback_query_handler(nopatr_handler, text = 'nopatr', state=Form.patronymic)
