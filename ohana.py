import telebot
from telebot import types
import sqlite3
import time
import datetime
import os
from telebot.types import InputMediaPhoto


sms_for_every_one = ""
photo_info = ""
file_directory = './menu_photos'
if not os.path.exists(file_directory):
    os.makedirs(file_directory)
days_of_week = ["Понедельник", "Вторник", "Среда", "Четверг", "Пятница", "Суббота", "Воскресенье"]
# Подключение к базе данных и создание таблиц
conn = sqlite3.connect("bd.db")
cursor = conn.cursor()
cursor.execute("CREATE TABLE IF NOT EXISTS users (id VARCHAR(20), name VARCHAR(50), phone VARCHAR(30))")
cursor.execute("CREATE TABLE IF NOT EXISTS books (id VARCHAR(20), name VARCHAR(50), phone VARCHAR(30), "
               "date VARCHAR(30), time VARCHAR(10), how_many INTEGER, extra TEXT, truly_is VARCHAR(10))")
cursor.execute("CREATE TABLE IF NOT EXISTS admins (id VARCHAR(20), name VARCHAR(100), status VARCHAR(10))")
cursor.execute("CREATE TABLE IF NOT EXISTS questions (id VARCHAR(20), name VARCHAR(100), text TEXT, "
               "answered VARCHAR(10))")
cursor.execute("SELECT id FROM admins WHERE name = ?", ("РАЗРАБ",))
new_admin_id = ""
person = cursor.fetchall()
if len(person) == 0:
    cursor.execute("INSERT INTO admins (id, name, status) VALUES (?, ?, ?)", ("7099912443", "РАЗРАБ", "TRUE"))
    print("succes")
conn.commit()

telegram_api = "7239804642:AAHB2FU8YJeW-keVDj2cuEEcFDBKnkbKCbA"
bot = telebot.TeleBot(telegram_api)


def do_list_of_admins():
    conn = sqlite3.connect("bd.db")
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM admins")
    list_of_admins = cursor.fetchall()
    a = []
    for i in list_of_admins:
        a.append(i[0])
    return a


def do_markup_for_admin():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("Меню")
    btn2 = types.KeyboardButton("Бронь")
    btn3 = types.KeyboardButton("Другие администраторы")
    btn4 = types.KeyboardButton("Посмотреть вопросы пользователей")
    btn5 = types.KeyboardButton("Сделать рассылку")
    markup.add(btn1)
    markup.add(btn2)
    markup.add(btn3)
    markup.add(btn4)
    markup.add(btn5)
    return markup


def do_group_media():
    list_of_photos = os.listdir(file_directory)
    media_group = []
    for photo in list_of_photos:
        media_group.append(InputMediaPhoto(open(f"{file_directory}/{photo}", "rb")))
    return media_group


@bot.message_handler(commands=['ask_question'])
def ask(message):
    name = get_name(str(message.chat.id))
    print(name)
    if name is not False:
        bot.send_message(message.chat.id, "Мы очень рады что у вас есть вопросы. Что вас интересует?")
        bot.register_next_step_handler(message, handle_ask)
    else:
        bot.send_message(message.chat.id, "К сожалению вы еще не зарегистрировались, чтобы задать вопрос.")


def handle_ask(message):
    text = message.text
    bot.send_message(message.chat.id, "Спасибо за вопрос! Скоро мы на него ответим...")
    conn = sqlite3.connect('bd.db')
    cursor = conn.cursor()
    name = get_name(str(message.chat.id))
    cursor.execute("INSERT INTO questions (id, name, text, answered) VALUES (?, ?, ?, ?)", (str(message.chat.id),
                                                                                            name, text, "FALSE"))
    conn.commit()
    conn.close()


def get_name(id):
    conn = sqlite3.connect('bd.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM users WHERE id = ?", (id,))
    a = cursor.fetchall()
    conn.close()
    if len(a) != 0:
        return a[0][0]
    return False





def send_photos(message):
    media_group = do_group_media()
    if len(media_group) == 0:
        if str(message.chat.id) in do_list_of_admins():
            bot.send_message(message.chat.id, "Меню нет. Пользователи не увидят меню. Чтобы это исправить создайте "
                                              "меню")
        else:
            bot.send_message(message.chat.id, "К сожалению меню отсутствует. Подождите совсем немного. Возможно,"
                                              "администрация меняет его прямо сейчас")
    else:
        bot.send_media_group(message.chat.id, media_group)


def delete_photo(num):
    photos = os.listdir(file_directory)
    os.remove(f"{file_directory}/{photos[num - 1]}")


def do_markup_for_menu():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    btn1 = types.KeyboardButton("Редактировать фотку")
    btn2 = types.KeyboardButton("Удалить фотку")
    btn3 = types.KeyboardButton("Добавить фотку")
    btn4 = types.KeyboardButton('Назад')
    markup.add(btn1, btn2, btn3, btn4)
    return markup


def asnwer(message, id, question):
    text = message.text
    if text == "Назад":
        markup = do_markup_for_admin()
        bot.send_message(message.chat.id, "Главное меню", reply_markup=markup)
    else:
        conn = sqlite3.connect('bd.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE questions SET answered = ? WHERE id = ?", ("TRUE", id,))
        conn.commit()
        conn.close()
        bot.send_message(id, f"Здравствуйте! Вы недавно спрашивали: {question}.\n\nОтвет от Администратора:{text}")
        do_list_of_questions(message)


def delete_admin(id):
    conn = sqlite3.connect('bd.db')
    cursor = conn.cursor()
    cursor.execute('DELETE FROM admins WHERE id = ?', (id,))
    conn.commit()
    conn.close()


@bot.callback_query_handler(func=lambda call: str(call.message.chat.id) in do_list_of_admins())
def get_call_from_admin(call):
    text = call.data
    chat_id = call.message.chat.id
    if "delete_book" in text:
        markup = types.InlineKeyboardMarkup(row_width=1)
        id = call.data.split('-')[1]
        btn1 = types.InlineKeyboardButton("Да, удалить", callback_data=f"truly_delete-{id}")
        btn2 = types.InlineKeyboardButton("Назад", callback_data=f"back-{id}")
        markup.add(btn1, btn2)
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=markup)
    elif "del_idmin" in text:
        id = call.data.split('-')[1]
        delete_admin(id)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        btn1 = types.KeyboardButton("Посмотреть меню")
        btn2 = types.KeyboardButton("Начать бронирование")
        markup.add(btn1, btn2)
        try:
            bot.send_message(id, "К сожалению вас убрали с должности Администратора в этом боте. Теперь вы можете "
                                 "забронировать стол", reply_markup=markup)
        except Exception as e:
            print(e)
        bot.send_message(chat_id, "Администратор был успешно удален")
        bot.delete_message(chat_id, call.message.message_id)
    elif "answer" in text:
        question = call.data.split('-')[2]
        id = call.data.split('-')[1]
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn = types.KeyboardButton("Назад")
        markup.add(btn)
        bot.send_message(chat_id, "Напишите ответ на вопрос...", reply_markup=markup)
        bot.register_next_step_handler(call.message, asnwer, id, question)
    elif "truly_delete" in text:
        id = call.data.split('-')[1]
        delete_book(id)
        do_list_of_books(call.message)
        bot.send_message(id, "Ваше бронирование больше не активно. Вы можете снова забронировать столик.")
    elif "back" in text:
        id = call.data.split('-')[1]
        markup = types.InlineKeyboardMarkup(row_width=1)
        btn1 = types.InlineKeyboardButton("Удалить бронирование", callback_data=f"delete_book-{id}")
        btn2 = types.InlineKeyboardButton("Редактировать бронирование", callback_data=f"redo_book-{id}")
        markup.add(btn2)
        markup.add(btn1)
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=markup)
    elif "redo_book" in text:
        id = call.data.split('-')[1]
        markup = do_markup_for_redo(id)
        bot.edit_message_reply_markup(chat_id, call.message.message_id, reply_markup=markup)
    elif "re_humans" in text:
        id = call.data.split('-')[1]
        markup = do_markup_for_how_many_people(id)
        bot.send_message(chat_id, "Сколько теперь будет человек?", reply_markup=markup)
    elif "new_people" in text:
        id = call.data.split('-')[2]
        number = call.data.split('-')[1]
        bot.delete_message(chat_id, message_id=call.message.message_id)
        update_book("how_many", number, id)
        do_list_of_books(call.message)
    elif "re_date" in text:
        id = call.data.split('-')[1]
        today = datetime.date.today()
        markup = types.InlineKeyboardMarkup()
        for i in range(7):
            days_to_add = datetime.timedelta(days=i)
            day = today + days_to_add
            day_name = days_of_week[day.weekday()]
            day_date = day.strftime("%d.%m")
            button_text = f"{day_name.capitalize()} {day_date}"
            btn = types.InlineKeyboardButton(button_text, callback_data=f"new_date-{day_date}-{day_name}-{id}")
            markup.add(btn)
        bot.send_message(call.message.chat.id, "Выберете новую дату для бронирования:", reply_markup=markup)
    elif "new_date" in text:
        id = call.data.split('-')[3]
        day_name = call.data.split('-')[2]
        day_date = call.data.split('-')[1]
        update_book("date", f"{day_date} {day_name}", id)
        bot.delete_message(chat_id, call.message.message_id)
        do_list_of_books(call.message)
    elif "re_pleasant" in text:
        id = call.data.split('-')[1]
        bot.send_message(chat_id, "Напишите новое пожелание к этому бронированию...")
        bot.register_next_step_handler(call.message, rewrite_pleasant, id)
    elif "re_time" in text:
        id = call.data.split('-')[1]
        today = datetime.date.today()
        date = call.data.split("-")[2]
        day = today.day
        month = today.month
        today_date = f"{day}.{month}"
        current_hour = datetime.datetime.now().hour
        markup = types.InlineKeyboardMarkup()
        if today_date == date:
            if current_hour < 11:
                start_hour = 12
            else:
                start_hour = current_hour + 1
        else:
            start_hour = 12
        end_hour = 24
        for hour in range(start_hour, end_hour + 1):
            if hour == 24:
                hour = "00"
            btn1 = types.InlineKeyboardButton(f"{hour}:00", callback_data=f"new_hour-{id}-{hour}")
            markup.add(btn1)
        bot.send_message(call.message.chat.id, "Выберете час бронирования", reply_markup=markup)
    elif "new_hour" in text:
        id = call.data.split('-')[1]
        hour = call.data.split("-")[2]
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton(f"{hour}:00", callback_data=f"minute-{hour}-00-{id}")
        btn2 = types.InlineKeyboardButton(f"{hour}:15", callback_data=f"minute-{hour}-15-{id}")
        btn3 = types.InlineKeyboardButton(f"{hour}:30", callback_data=f"minute-{hour}-30-{id}")
        btn4 = types.InlineKeyboardButton(f"{hour}:45", callback_data=f"minute-{hour}-45-{id}")
        markup.add(btn1)
        markup.add(btn2)
        markup.add(btn3)
        markup.add(btn4)
        bot.send_message(call.message.chat.id, f"час бронирования | {hour}:00")
        bot.delete_message(call.message.chat.id, call.message.message_id)
        bot.send_message(call.message.chat.id, "Отлично! Теперь выберете минуту...", reply_markup=markup)
    elif "minute" in text:
        id = call.data.split('-')[3]
        hour = call.data.split("-")[1]
        minute = call.data.split("-")[2]
        update_book("time", f"{hour}:{minute}", id)
        bot.delete_message(chat_id, call.message.message_id)
        do_list_of_books(call.message)









def do_markup_for_redo(id):
    markup = types.InlineKeyboardMarkup(row_width=1)
    date = do_list_of_book_info(id)[3][0:5]
    print(date)
    btn1 = types.InlineKeyboardButton("Поменять кол-во человек", callback_data=f"re_humans-{id}")
    btn2 = types.InlineKeyboardButton("Поменять дату", callback_data=f"re_date-{id}")
    btn3 = types.InlineKeyboardButton("Поменять время", callback_data=f"re_time-{id}-{date}")
    btn4 = types.InlineKeyboardButton("Поменять пожелание", callback_data=f"re_pleasant-{id}")
    btn5 = types.InlineKeyboardButton("Назад", callback_data=f"back-{id}")
    markup.add(btn1, btn2, btn3, btn4, btn5)
    return markup


def rewrite_pleasant(message, id):
    text = message.text
    update_book("extra", text, id)
    do_list_of_books(message)


def do_markup_for_how_many_people(id):
    markup = types.InlineKeyboardMarkup()
    for i in range(0, 9, 3):
        btn1 = types.InlineKeyboardButton(f"{i + 1}", callback_data=f"new_people-{i + 1}-{id}")
        btn2 = types.InlineKeyboardButton(f"{i + 2}", callback_data=f"new_people-{i + 2}-{id}")
        btn3 = types.InlineKeyboardButton(f"{i + 3}", callback_data=f"new_people-{i + 3}-{id}")
        markup.add(btn1, btn2, btn3)
    return markup







@bot.message_handler(func=lambda message: str(message.chat.id) in do_list_of_admins())
def admin_btn(message):
    text = message.text
    global sms_for_every_one
    if text == "Меню":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        btn1 = types.KeyboardButton("Назад")
        btn2 = types.KeyboardButton("Редактировать")
        markup.add(btn2, btn1)
        bot.send_message(message.chat.id, "Вот меню в кальянной Охана...", reply_markup=markup)
        send_photos(message)
    elif text == "Редактировать":
        markup = do_markup_for_menu()
        bot.send_message(message.chat.id, "Что вы хотите сделать с фоткой(-ами)?", reply_markup=markup)
    elif text == "Удалить фотку":
        send_photos(message)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        group_media = do_group_media()
        for i in range(len(group_media)):
            btn = types.KeyboardButton(f"Удалить фотку №{i + 1}")
            markup.add(btn)
        btn = types.KeyboardButton("Назад")
        markup.add(btn)
        bot.send_message(message.chat.id, "Какую фотку вы хотите удалить?", reply_markup=markup)
    elif "Посмотреть вопросы пользователей" == text:
        do_list_of_questions(message)
    elif text == "Сделать рассылку":
        bot.send_message(message.chat.id, "Пожалуйста, напишите текст для рассылки в боте всем пользователям")
        bot.register_next_step_handler(message, write_sms_for_every_users)
    elif "Удалить фотку №" in text:
        number = int(text.split("№")[1])
        print("delete", number)
        n1 = os.listdir(file_directory)
        delete_photo(number)
        n2 = os.listdir(file_directory)
        if len(n1) != len(n2):
            bot.send_message(message.chat.id, "Фотка была успешно удалена")
        else:
            bot.send_message(message.chat.id, "Ошибка! Не удалось удалить фотку")
        send_photos(message)
    elif text == "Бронь":
        do_list_of_books(message)
    elif text == "Другие администраторы":
        do_list_of_other_admins(message)
    elif text == "Назад" or text == "Главное меню":
        markup = do_markup_for_admin()
        bot.send_message(message.chat.id, "Главное меню", reply_markup=markup)
    elif text == "Добавить фотку":
        markup = types.ReplyKeyboardRemove()
        bot.send_message(message.chat.id, "Скиньте фотку меню", reply_markup=markup)
        bot.register_next_step_handler(message, handle_photo_for_menu)
    elif text == "Редактировать фотку":
        send_photos(message)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        group_media = do_group_media()
        for i in range(len(group_media)):
            btn = types.KeyboardButton(f"Редактировать фотку №{i + 1}")
            markup.add(btn)
        btn = types.KeyboardButton("Назад")
        markup.add(btn)
        bot.send_message(message.chat.id, "Какую фотку вы хотите редактировать?", reply_markup=markup)
    elif "Редактировать фотку №" in text:
        markup = types.ReplyKeyboardRemove()
        bot.send_message(message.chat.id, "Скиньте фотку меню, вместо выбранного", reply_markup=markup)
        number = int(text.split("№")[1])
        bot.register_next_step_handler(message, handle_photo_to_redact, number)
    elif "Добавить администратора" == text:
        bot.send_message(message.chat.id, "Введите telegram-id пользователя (Например: 984914418). Его можно взять "
                                          "из этого бота @getmyid_bot или в любом другом похожем боте")
        bot.register_next_step_handler(message, handle_id)
    elif text == "С картинкой":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("Без картинки")
        btn2 = types.KeyboardButton("Главное меню")
        markup.add(btn1)
        markup.add(btn2)
        bot.send_message(message.chat.id, "Скиньте картинку", reply_markup=markup)
        bot.register_next_step_handler(message, handle_photo)
    elif text == "Без картинки":
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        btn1 = types.KeyboardButton("Разослать всем пользователям")
        btn2 = types.KeyboardButton("Назад")
        markup.add(btn1)
        markup.add(btn2)
        bot.send_message(message.chat.id, "Хорошо! Нажмите на кнопку ниже и рассылка отправиться всем пользователям",
                         reply_markup=markup)
    elif text == "Скинуть всем пользователям":
        do_sms_for_every_users(sms_for_every_one, photo_info, message)
    elif text == "Разослать всем пользователям":
        do_sms_for_every_users(sms_for_every_one, 0, message)
        sms_for_every_one = ""


def do_sms_for_every_users(text, id_of_photo, message):
    markup = do_markup_for_admin()
    try:
        conn = sqlite3.connect("bd.db")
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users")
        list_of_all_users = cursor.fetchall()
        admin_list = do_list_of_admins()
        conn.close()
        if id_of_photo != 0:
            for id in list_of_all_users:
                if str(id[0]) not in admin_list:
                    print(id)
                    bot.send_photo(id[0], id_of_photo, text)
        else:
            for id in list_of_all_users:
                if str(id[0]) not in admin_list:
                    print(id)
                    bot.send_message(id[0], text)
        bot.send_message(message.chat.id, "Рассылка успешно была отправлена", reply_markup=markup)
    except Exception as e:
        bot.send_message(message.chat.id, "Ошибка в рассылке:\n\n" + str(e), reply_markup=markup)


def write_sms_for_every_users(message):
    global sms_for_every_one
    text = message.text
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    btn1 = types.KeyboardButton("С картинкой")
    btn2 = types.KeyboardButton("Без картинки")
    markup.add(btn1)
    markup.add(btn2)
    sms_for_every_one = text
    bot.send_message(message.chat.id, "Текст готов! Будет ли наша рассылка с картинкой?", reply_markup=markup)


def handle_photo(message):
    global sms_for_every_one, photo_info
    if message.content_type == "photo":
        photo_info = message.photo[-1].file_id
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        btn1 = types.KeyboardButton("Скинуть всем пользователям")
        btn2 = types.KeyboardButton("Главное меню")
        markup.add(btn1, btn2)
        bot.send_message(message.chat.id, "Подтвердите рассылку...", reply_markup=markup)
    else:
        admin_btn(message)


def do_list_of_questions(message):
    conn = sqlite3.connect('bd.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM questions WHERE answered = ?", ("FALSE",))
    a = cursor.fetchall()
    print(a)
    for i in a:
        id = i[0]
        markup = types.InlineKeyboardMarkup()
        btn = types.InlineKeyboardButton("Ответить на вопрос", callback_data=f"answer-{id}-{i[2]}")
        markup.add(btn)
        text = f"{i[1]} Спрашивает:\n\n '{i[2]}'"
        bot.send_message(message.chat.id, text, reply_markup=markup)
    markup = do_markup_for_admin()
    bot.send_message(message.chat.id, f"Всего не отвеченных вопросов {len(a)}", reply_markup=markup)


def add_new_admin(name, id):
    conn = sqlite3.connect('bd.db')
    cursor = conn.cursor()
    print(id, name)
    markup = do_markup_for_admin()
    try:
        bot.send_message(id, "Вы стали администратором в этом боте!", reply_markup=markup)
        cursor.execute("INSERT INTO admins (id, name, status) VALUES (?, ?, ?)", (id, name, "TRUE"))
        conn.commit()
    except Exception as e:
        print(e)
    conn.close()


def handle_id(message):
    text = message.text
    markup = types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id, "Отлично! Теперь введите имя нового администратора", reply_markup=markup)
    bot.register_next_step_handler(message, handle_name, text)


def handle_name(message, id): x
    name = message.text
    add_new_admin(name, id)
    do_list_of_other_admins(message)



def do_list_of_other_admins(message):
    conn = sqlite3.connect('bd.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM admins WHERE status = ?", ("TRUE",))
    list_of_admins = cursor.fetchall()
    conn.close()
    my_id = str(message.chat.id)
    for admin in list_of_admins:
        print(admin)
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("Удалить администратора", callback_data=f"del_idmin-{admin[0]}")

        if admin[0] != my_id:
            markup.add(btn1)
        text = f"Администратор: {admin[1]}"
        bot.send_message(message.chat.id, text, reply_markup=markup)
    markup = do_markup_for_add_admin()
    bot.send_message(message.chat.id, f"Всего администраторов: {len(list_of_admins)}", reply_markup=markup)


def do_markup_for_add_admin():
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    btn1 = types.KeyboardButton("Добавить администратора")
    btn2 = types.KeyboardButton("Назад")
    markup.add(btn1, btn2)
    return markup





def do_list_of_books(message):
    conn = sqlite3.connect('bd.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM books WHERE truly_is = ?", ("TRUE",))
    a = cursor.fetchall()
    print(a)
    if len(a) != 0:
        for list_of_book_info in a:
            markup = types.InlineKeyboardMarkup(row_width=1)
            btn1 = types.InlineKeyboardButton("Удалить бронирование", callback_data=f"delete_book-"
                                                                                    f"{list_of_book_info[0]}")
            btn2 = types.InlineKeyboardButton("Редактировать бронирование", callback_data=f"redo_book-"
                                                                                          f"{list_of_book_info[0]}")
            markup.add(btn2)
            markup.add(btn1)
            text = ""
            for i in range(1, len(list_of_book_info) - 1):
                if list_of_book_info[i] is None:
                    continue
                if i == 1:
                    text += f"Имя: {list_of_book_info[i]}\n"
                elif i == 2:
                    text += f"Номер телефона: {list_of_book_info[i]}\n"
                elif i == 3:
                    text += f"Дата: {list_of_book_info[i]}\n"
                elif i == 4:
                    text += f"Время: {list_of_book_info[i]}\n"
                elif i == 5:
                    text += f"Кол-во персон: {list_of_book_info[i]}\n"
                elif i == 6:
                    text += f"Пожелания к бронированию: {list_of_book_info[i]}\n"
            bot.send_message(message.chat.id, text, reply_markup=markup)
        bot.send_message(message.chat.id, f"Забронированных столов: {len(a)}")
    else:
        bot.send_message(message.chat.id, "Бронированных столов нет")



def handle_photo_to_redact(message, num):
    if message.photo:
        photo = message.photo[-1]
        delete_photo(num)
        file_info = bot.get_file(photo.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        save_path = f"{file_directory}/menu{num - 1}.png"
        with open(save_path, "wb") as new_file:
            new_file.write(downloaded_file)
        markup = do_markup_for_menu()
        bot.send_message(message.chat.id, "Фотография сохранена!", reply_markup=markup)
        send_photos(message)
    else:
        markup = do_markup_for_menu()
        bot.send_message(message.chat.id, "Это не фотка", reply_markup=markup)



def handle_photo_for_menu(message):
    if message.photo:
        photo = message.photo[-1]
        length_of_photos = len(os.listdir(file_directory))
        file_info = bot.get_file(photo.file_id)
        downloaded_file = bot.download_file(file_info.file_path)
        save_path = f"{file_directory}/menu{length_of_photos - 1}.png"
        with open(save_path, "wb") as new_file:
            new_file.write(downloaded_file)
        markup = do_markup_for_menu()
        bot.send_message(message.chat.id, "Фотография сохранена!", reply_markup=markup)
        send_photos(message)
    else:
        markup = do_markup_for_menu()
        bot.send_message(message.chat.id, "Это не фотка", reply_markup=markup)


# Стартовый обработчик
@bot.message_handler(commands=['start'])
def start(message):
    print(do_list_of_admins())
    if str(message.chat.id) in do_list_of_admins():
        markup = do_markup_for_admin()
        bot.send_message(message.chat.id, "Приветствую администратор!", reply_markup=markup)
    else:
        if not is_user_already_created(str(message.chat.id)):
            print(is_user_already_created(str(message.chat.id)))
            bot.send_message(message.chat.id, "Здравствуйте! Мы рады приветствовать Вас в Охане🏄‍♂️\n"
                                              "Для продолжения бронирования, пожалуйста, укажите ваше имя.")
            bot.register_next_step_handler(message, ask_name)
        else:
            bot.send_message(message.chat.id, "Вы уже зарегистрировались в боте! Если у вас есть вопросы по "
                                              "командам в боте, нажмите /help")


@bot.message_handler(commands=["do_book"])
def start_book(message):
    if is_user_already_created(str(message.chat.id)):
        start_answers(message, message.chat.id)
    else:
        bot.send_message(message.chat.id, "Здравствуйте! Мы рады приветствовать Вас в Охане🏄‍♂️\n"
                                          "Для продолжения бронирования, пожалуйста, укажите ваше имя.")
        bot.register_next_step_handler(message, ask_name)

def start_answers(message, id):
    list_of_book_info = do_list_of_book_info(id)
    print(list_of_book_info)
    if list_of_book_info is False:
        name = take_name_from_bd(str(id))
        phone = take_phone_from_bd(str(id))
        create_book(str(id), name, phone)
        markup = types.ReplyKeyboardRemove()
        bot.send_message(message.chat.id, f"Здравствуйте, {name}! "
                                          f"Давайте начнем бронирование в кальянной Охана!", reply_markup=markup)
        markup = types.InlineKeyboardMarkup()
        for i in range(0, 9, 3):
            btn1 = types.InlineKeyboardButton(f"{i + 1}", callback_data="how_many-" + str(i + 1) + "-" +
                                                                        str(id))
            btn2 = types.InlineKeyboardButton(f"{i + 2}", callback_data="how_many-" + str(i + 2) + "-" +
                                                                        str(id))
            btn3 = types.InlineKeyboardButton(f"{i + 3}", callback_data="how_many-" + str(i + 3) + "-" +
                                                                        str(id))
            markup.add(btn1, btn2, btn3)
        bot.send_message(message.chat.id, "Сколько Вас будет человек?", reply_markup=markup)
    else:
        bot.send_message(message.chat.id, "У вас уже есть активное бронирование.")





def create_book(id, name, phone):
    conn = sqlite3.connect('bd.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO books (id, name, phone, truly_is) VALUES (?, ?, ?, ?)", (id, name, phone, "FALSE"))
    conn.commit()
    conn.close()


def update_book(column, thing, id):
    conn = sqlite3.connect('bd.db')
    cursor = conn.cursor()
    cursor.execute(f"UPDATE books SET {column} = ? WHERE id = ?", (thing, id))
    conn.commit()
    conn.close()


@bot.callback_query_handler(func=lambda call: str(call.message.chat.id) not in do_list_of_admins())
def get_call(call):
    if "create_book" in call.data:
        id = call.data.split("-")[1]
        if is_book_true(id):
            bot.send_message(call.message.chat.id, "Кнопки больше не действуют. У вас уже есть забронированный стол")
        else:
            start_answers(call.message, id)
    elif "how_many" in call.data:
        if len(call.data.split("-")) == 3:
            id = call.data.split("-")[2]
        else:
            id = call.data.split("-")[1]
        if is_book_true(id):
            bot.send_message(call.message.chat.id, "Кнопки больше не действуют. У вас уже есть забронированный стол")
        else:
            quantity = ""
            today = datetime.date.today()
            if len(call.data.split("-")) == 3:
                quantity = int(call.data.split("-")[1])
                update_book("how_many", quantity, id)
            markup = types.InlineKeyboardMarkup()
            for i in range(7):
                days_to_add = datetime.timedelta(days=i)
                day = today + days_to_add
                day_name = days_of_week[day.weekday()]
                day_date = day.strftime("%d.%m")
                button_text = f"{day_name.capitalize()} {day_date}"
                btn = types.InlineKeyboardButton(button_text, callback_data=f"day-{day_date}-{day_name}-{id}")
                markup.add(btn)
            if len(call.data.split("-")) == 3:
                bot.send_message(call.message.chat.id, f"Хорошо! Кол-во человек: {quantity}")
                bot.delete_message(call.message.chat.id, call.message.message_id)
                bot.send_message(call.message.chat.id, "Выберете дату бронирования", reply_markup=markup)
            else:
                bot.send_message(call.message.chat.id, "Выберете новую дату для бронирования:", reply_markup=markup)
    elif "day" in call.data:
        id = call.data.split("-")[3]
        if is_book_true(id):
            bot.send_message(call.message.chat.id, "Кнопки больше не действуют. У вас уже есть забронированный стол")
        else:
            today = datetime.date.today()
            date = call.data.split("-")[1]
            day = today.day
            month = today.month
            today_date = f"{day}.{month}"
            current_hour = datetime.datetime.now().hour
            day_name = call.data.split("-")[2]
            update_book("date", f"{date} {day_name}", id)
            bot.send_message(call.message.chat.id, f"Отлично! Дата выбрана. ({date}|{day_name})")
            bot.delete_message(call.message.chat.id, call.message.message_id)
            markup = types.InlineKeyboardMarkup()
            print(current_hour)
            if today_date == date:
                if current_hour < 11:
                    start_hour = 12
                else:
                    start_hour = current_hour + 1
            else:
                start_hour = 12
            end_hour = 24
            if len(call.data.split("-")) == 4:
                for hour in range(start_hour, end_hour + 1):
                    btn1 = types.InlineKeyboardButton(f"{hour}:00", callback_data=f"hour-{hour}-{id}")
                    markup.add(btn1)
                bot.send_message(call.message.chat.id, "Выберете час бронирования", reply_markup=markup)
            else:
                for hour in range(start_hour, end_hour + 1):
                    btn1 = types.InlineKeyboardButton(f"{hour}:00", callback_data=f"hour-{hour}-{id}-1")
                    markup.add(btn1)
                bot.send_message(call.message.chat.id, "Выберите новый час бронирования", reply_markup=markup)
    elif "hour" in call.data:
        id = call.data.split("-")[2]
        if is_book_true(id):
            bot.send_message(call.message.chat.id, "Кнопки больше не действуют. У вас уже есть забронированный стол")
        else:
            hour = call.data.split("-")[1]
            markup = types.InlineKeyboardMarkup()
            btn1 = types.InlineKeyboardButton(f"{hour}:00", callback_data=f"minute-{hour}-00-{id}")
            btn2 = types.InlineKeyboardButton(f"{hour}:{15}", callback_data=f"minute-{hour}-15-{id}")
            btn3 = types.InlineKeyboardButton(f"{hour}:{30}", callback_data=f"minute-{hour}-30-{id}")
            btn4 = types.InlineKeyboardButton(f"{hour}:{45}", callback_data=f"minute-{hour}-45-{id}")
            markup.add(btn1)
            markup.add(btn2)
            markup.add(btn3)
            markup.add(btn4)
            bot.send_message(call.message.chat.id, f"час бронирования | {hour}:00")
            bot.delete_message(call.message.chat.id, call.message.message_id)
            bot.send_message(call.message.chat.id, "Отлично! Теперь выберете минуту...", reply_markup=markup)
    elif "minute"in call.data:
        id = call.data.split("-")[3]
        if is_book_true(id):
            bot.send_message(call.message.chat.id, "Кнопки больше не действуют. У вас уже есть забронированный стол")
        else:
            hour = call.data.split("-")[1]
            minute = call.data.split("-")[2]
            update_book("time", f"{hour}:{minute}", id)
            do_info(call.message, id)
    elif "back" in call.data:
        id = call.data.split("-")[1]
        if is_book_true(id):
            bot.send_message(call.message.chat.id, "Кнопки больше не действуют. У вас уже есть забронированный стол")
        else:
            list_of_book_info = do_list_of_book_info(id)
            markup = types.InlineKeyboardMarkup()
            btn1 = types.InlineKeyboardButton("Редактировать | Удалить", callback_data=f"re-{id}")
            btn2 = types.InlineKeyboardButton("Убрать пожелание", callback_data=f"pleas_del-{id}")
            btn3 = types.InlineKeyboardButton("Написать пожелания к бронированию", callback_data=f"write_pleasant-{id}")
            btn4 = types.InlineKeyboardButton("Редактировать пожелания к бронированию",
                                              callback_data=f"write_pleasant-{id}")
            btn6 = types.InlineKeyboardButton("Закончить бронирование", callback_data=f"finish-{id}")
            markup.add(btn1)
            if None not in list_of_book_info:
                markup.add(btn2)
                markup.add(btn4)
            else:
                markup.add(btn3)
            markup.add(btn6)
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=markup)
    elif "new_quantity" in call.data:
        id = call.data.split("-")[2]
        if is_book_true(id):
            bot.send_message(call.message.chat.id, "Кнопки больше не действуют. У вас уже есть забронированный стол")
        else:
            quantity = call.data.split("-")[1]
            update_book("how_many", quantity, id)
            do_info(call.message, id)
    elif "pleas_del" in call.data:
        id = call.data.split("-")[1]
        if is_book_true(id):
            bot.send_message(call.message.chat.id, "Кнопки больше не действуют. У вас уже есть забронированный стол")
        else:
            update_book("extra", None, id)
            do_info(call.message, id)
            do_info(call.message, id)
    elif "requa" in call.data:
        id = call.data.split("-")[1]
        if is_book_true(id):
            bot.send_message(call.message.chat.id, "Кнопки больше не действуют. У вас уже есть забронированный стол")
        else:
            markup = types.InlineKeyboardMarkup()
            for i in range(0, 9, 3):
                btn1 = types.InlineKeyboardButton(f"{i + 1}", callback_data="new_quantity-" + str(i + 1) + "-" + id)
                btn2 = types.InlineKeyboardButton(f"{i + 2}", callback_data="new_quantity-" + str(i + 2) + "-" + id)
                btn3 = types.InlineKeyboardButton(f"{i + 3}", callback_data="new_quantity-" + str(i + 3) + "-" + id)
                markup.add(btn1, btn2, btn3)
            bot.send_message(call.message.chat.id, "Сколько Вас будет человек?", reply_markup=markup)
    elif "is_delete" in call.data:
        id = call.data.split("-")[1]
        if is_book_true(id):
            bot.send_message(call.message.chat.id, "Кнопки больше не действуют. У вас уже есть забронированный стол")
        else:
            markup = types.InlineKeyboardMarkup()
            btn1 = types.InlineKeyboardButton("Удалить", callback_data=f"delete-{id}")
            btn2 = types.InlineKeyboardButton("Назад", callback_data=f"re-{id}")
            markup.add(btn1)
            markup.add(btn2)
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=markup)
    elif "delete" in call.data:
        id = call.data.split("-")[1]
        if is_book_true(id):
            bot.send_message(call.message.chat.id, "Кнопки больше не действуют. У вас уже есть забронированный стол")
        else:
            delete_book(id)
            markup = types.InlineKeyboardMarkup()
            btn = types.InlineKeyboardButton("Создать новое бронирование", callback_data=f"create_book-{id}")
            markup.add(btn)
            bot.send_message(call.message.chat.id, "Вы удалили незаконченное бронирование. Можете сделать новое н"
                                                   "ажав на кнопку...", reply_markup=markup)
    elif "re" in call.data:
        id = call.data.split("-")[1]
        if is_book_true(id):
            bot.send_message(call.message.chat.id, "Кнопки больше не действуют. У вас уже есть забронированный стол")
        else:
            markup = types.InlineKeyboardMarkup()
            btn1 = types.InlineKeyboardButton("Поменять время бронирования", callback_data=f"how_many-{id}")
            btn3 = types.InlineKeyboardButton("Поменять кол-во", callback_data=f"requantity-{id}")
            btn4 = types.InlineKeyboardButton("Удалить всё", callback_data=f"is_delete-{id}")
            btn5 = types.InlineKeyboardButton("Назад", callback_data=f"back-{id}")
            markup.add(btn1)
            markup.add(btn3)
            markup.add(btn4)
            markup.add(btn5)
            bot.edit_message_reply_markup(call.message.chat.id, call.message.message_id, reply_markup=markup)
    elif "write_pleasant" in call.data:
        id = call.data.split("-")[1]
        if is_book_true(id):
            bot.send_message(call.message.chat.id, "Кнопки больше не действуют. У вас уже есть забронированный стол")
        else:
            send_photos(call.message)
            bot.send_message(call.message.chat.id, "Напишите пожелания к бронированию, например, что вы хотите")
            bot.register_next_step_handler(call.message, write_ples, id)
    elif "finish" in call.data:
        id = call.data.split("-")[1]
        if is_book_true(id):
            bot.send_message(call.message.chat.id, "Кнопки больше не действуют. У вас уже есть забронированный стол")
        else:
            list_of_book_info = do_list_of_book_info(id)
            update_book("truly_is", "TRUE", id)
            bot.send_message(call.message.chat.id, f"Бронирование успешно завершено! "
                                                   f"Скоро на номер {list_of_book_info[2]}"
                                                   f" позвонит администратор")
    else:
        bot.send_message(call.message.chat.id, "error with data")


def is_book_true(id):
    conn = sqlite3.connect("bd.db")
    cursor = conn.cursor()
    cursor.execute("SELECT truly_is FROM books WHERE id = ?", (str(id),))
    a = cursor.fetchall()
    conn.close()
    print(a)
    if len(a) != 0:
        if a[0][0] == "FALSE":
            return False
        elif a[0][0] == "TRUE":
            return True
    else:
        return False


def write_ples(message, id):
    text = message.text
    update_book("extra", text, id)
    do_info(message, id)


def delete_book(id):
    conn = sqlite3.connect("bd.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM books WHERE id = ?", (str(id),))
    conn.commit()
    conn.close()


def do_info(message, id):
    bot.delete_message(message.chat.id, message.message_id)
    list_of_book_info = do_list_of_book_info(id)
    print(list_of_book_info)
    if list_of_book_info is False:
        bot.send_message(message.chat.id, "error with text")
    else:
        text = ""
        for i in range(1, len(list_of_book_info) - 1):
            if list_of_book_info[i] is None:
                continue
            if i == 1:
                text += f"Имя: {list_of_book_info[i]}\n"
            elif i == 2:
                text += f"Номер телефона: {list_of_book_info[i]}\n"
            elif i == 3:
                text += f"Дата: {list_of_book_info[i]}\n"
            elif i == 4:
                text += f"Время: {list_of_book_info[i]}\n"
            elif i == 5:
                text += f"Кол-во персон: {list_of_book_info[i]}\n"
            elif i == 6:
                text += f"Пожелания к бронированию: {list_of_book_info[i]}\n"
        markup = types.InlineKeyboardMarkup()
        btn1 = types.InlineKeyboardButton("Редактировать | Удалить", callback_data=f"re-{id}")
        btn2 = types.InlineKeyboardButton("Убрать пожелание", callback_data=f"pleas_del-{id}")
        btn3 = types.InlineKeyboardButton("Написать пожелания к бронированию", callback_data=f"write_pleasant-{id}")
        btn4 = types.InlineKeyboardButton("Редактировать пожелания к бронированию", callback_data=f"write_pleasant-{id}")
        btn6 = types.InlineKeyboardButton("Закончить бронирование", callback_data=f"finish-{id}")
        markup.add(btn1)
        if None not in list_of_book_info:
            markup.add(btn2)
            markup.add(btn4)
        else:
            markup.add(btn3)
        markup.add(btn6)
        bot.send_message(message.chat.id, f"Отлично всё готово! Вот вся информация о брони:\n\n{text}",
                         reply_markup=markup)


def do_list_of_book_info(id):
    conn = sqlite3.connect('bd.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM books WHERE id = ?", (id,))
    a = cursor.fetchall()
    conn.close()
    if len(a) != 0:
        return a[0]
    return False


# Обработка введенного имени и запрос номера телефона
def ask_name(message):
    user_name = message.text
    user_id = message.chat.id

    # Сохраняем имя пользователя во временную таблицу (или можно использовать переменные)
    conn = sqlite3.connect('bd.db')
    cursor = conn.cursor()
    cursor.execute("INSERT INTO users (id, name) VALUES (?, ?)",
                   (user_id, user_name))
    conn.commit()

    # Спрашиваем номер телефона
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    phone_button = types.KeyboardButton(text="Скинуть номер телефона этого аккаунта", request_contact=True)
    btn2 = types.KeyboardButton("Нет, написать другой")
    markup.add(phone_button)
    markup.add(btn2)

    bot.send_message(message.chat.id, f"{user_name}, теперь поделитесь номером телефона для завершения бронирования.",
                     reply_markup=markup)


def take_name_from_bd(id):
    conn = sqlite3.connect('bd.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM users WHERE id = ?", (id,))
    person = cursor.fetchall()
    if len(person) == 0:
        return False
    return person[0][0]


def take_phone_from_bd(id):
    conn = sqlite3.connect('bd.db')
    cursor = conn.cursor()
    cursor.execute("SELECT phone FROM users WHERE id = ?", (id,))
    person = cursor.fetchall()
    if len(person) == 0:
        return False
    return person[0][0]


def is_user_already_created(id):
    conn = sqlite3.connect('bd.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM users WHERE id = ?", (id,))
    person = cursor.fetchall()
    conn.close()
    if len(person) == 0:
        return False
    return True



# Обрабатываем номер телефона (через контакт)
@bot.message_handler(content_types=['contact'])
def handle_contact(message):
    if message.contact is not None:
        user_id = message.chat.id
        phone = message.contact.phone_number

        # Сохраняем номер телефона в базу данных
        conn = sqlite3.connect('bd.db')
        cursor = conn.cursor()
        cursor.execute("UPDATE users SET phone = ? WHERE id = ?", (phone, user_id))
        conn.commit()
        markup = types.ReplyKeyboardRemove()
        bot.send_message(message.chat.id, f"Спасибо! Ваш номер {phone} был сохранен в системе.", reply_markup=markup)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        btn1 = types.KeyboardButton("Посмотреть меню")
        btn2 = types.KeyboardButton("Начать бронирование")
        markup.add(btn1, btn2)
        bot.send_message(message.chat.id,
                         "Хотите посмотреть меню или сразу забронировать стол?", reply_markup=markup)

# Если пользователь выбрал опцию "Нет, написать другой", то вводим номер вручную
@bot.message_handler(func=lambda message: message.text == "Нет, написать другой")
def ask_for_phone_number(message):
    if not is_user_already_created(str(message.chat.id)):
        markup = types.ReplyKeyboardRemove()
        bot.send_message(message.chat.id, "Пожалуйста, введите ваш номер телефона вручную:", reply_markup=markup)
        bot.register_next_step_handler(message, handle_manual_phone)
    else:
        bot.send_message(message.chat.id, "Вы уже зарегистрировались в боте! Если у вас есть вопросы по "
                                          "командам в боте, нажмите /help")


@bot.message_handler(commands=['help'])
def help(message):
    bot.send_message(message.chat.id, "/help - посмотреть все функции\n"
                                      "/do_book - Начать бронирование\n"
                                      "/ask_question - Задать вопрос\n"
                                      "/menu - Посмотреть меню")


@bot.message_handler(commands=['menu'])
def menu(message):
    send_photos(message)



@bot.message_handler(func=lambda message: str(message.chat.id) not in do_list_of_admins())
def get_message(message):
    text = message.text
    if text == "Посмотреть меню":
        send_photos(message)
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
        btn = types.KeyboardButton("Начать бронирование")
        markup.add(btn)
        bot.send_message(message.chat.id, "Вот Наше меню. Хотите начать бронирование?", reply_markup=markup)
    elif text == "Начать бронирование":
        start_answers(message, str(message.chat.id))



# Обрабатываем вручной ввод номера
def handle_manual_phone(message):
    phone = message.text
    user_id = message.chat.id

    # Сохраняем вручной номер телефона в базу данных
    conn = sqlite3.connect('bd.db')
    cursor = conn.cursor()
    cursor.execute("UPDATE users SET phone = ? WHERE id = ?", (phone, user_id))
    conn.commit()
    markup = types.ReplyKeyboardRemove()
    bot.send_message(message.chat.id, f"Спасибо! Ваш номер {phone} был сохранен в системе.", reply_markup=markup)
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True, row_width=1)
    btn1 = types.KeyboardButton("Посмотреть меню")
    btn2 = types.KeyboardButton("Начать бронирование")
    markup.add(btn1, btn2)
    bot.send_message(message.chat.id,
                     "Хотите посмотреть меню или сразу забронировать стол?", reply_markup=markup)

# Основной цикл работы бота
while True:
    try:
        bot.polling(none_stop=True)
    except Exception as e:
        print(e)
        time.sleep(15)
