# Импортируем модуль для создания календаря
from telegram_bot_calendar import DetailedTelegramCalendar, LSTEP
# Импортируем модуль для создания бота
import telebot
# Импgортируем модуль для работы с потоками
import threading
# Импортируем модуль для работы со временем
import datetime
# Импортируем токен и имя БД
import config
# Импортуруем модуль для работы с БД
from SQL_file import SQLighter
# Импортируем модуль для создания пользователей
from users import Users_list
# Импортируем набор созданных клавиатур и индентификаторы их клавиш
from keyboards import keyboard_menu, kb_hours, kb_minutes_page1, kb_minutes_page2, \
    kb_priority, keyboard_upd, kb_choice, kb_time_zone, time_zone_id, \
    hours_id_list, minutes_list_1, minutes_list_2, keyboard_upd_id, priority_list

# Сопоставляем русские названия "год, месяц, день" с английскими для календаря
LSTEP = {'y': 'год', 'm': 'месяц', 'd': 'день'}
# Инициализируем бота
bot = telebot.TeleBot(
    config.token
)
# Инциализируем соединение с таблицей событий
schedule = SQLighter(
    config.database_name
)
# Инциализируем соединение с таблицей пользователей
users = Users_list(
    config.database_name
)


# Функция для перехода к календарю с выбором дня
def choose_date(message):
    calendar, step = DetailedTelegramCalendar().build()
    bot.send_message(
        message.chat.id,
        "Выберите день:",
        reply_markup=calendar
    )


# Функция показывающая список событий в указанный день
def show_events_list(c, key, date, events_list):
    bot.send_message(
        c.message.chat.id,
        f"Вы выбрали {date}. Вот список ваших событий в этот день:",
        reply_markup=key
    )
    for event in events_list:
        time_b, time_e, nam, descr, prio = event
        bot.send_message(
            c.message.chat.id,
            f"Событие запланировано на {time_b}-{time_e}\n"
            f"Название: {nam}\n"
            f"Описание: {descr}\n"
            f"Приоретет: {prio}"
        )


# Функция проверяющая есть ли события в этот день и отвечающая пользователю в зависимости от статуса
def calendar_ans(c, u_id, result_date, key, mess, keyboard=None):
    # Получаем кортеж с кортежами событий в формате: время начала, время конца
    # имя, описание, приоретет. Проверяем есть ли события в этот день
    events_list = schedule.select_all_events(
        u_id,
        result_date
    )
    if len(
            events_list
    ) == 0:
        bot.edit_message_text(
            f"Вы выбрали {result_date}. Кажется на этот день вы ничего не планировали.",
            c.message.chat.id,
            c.message.message_id,
            reply_markup=key
        )
        # Возвращаем статус пользователя в исходный пустой
        users.update_user(
            u_id,
            "user_states",
            ""
        )

    else:
        show_events_list(
            c,
            key,
            result_date,
            events_list
        )
        bot.send_message(
            c.message.chat.id,
            mess,
            reply_markup=keyboard
        )


def time_zone_choose(message, u_id):
    # Определяем смещение времени пользователя относительно сервера
    users.update_user(
        u_id,
        "time_zone",
        "time_choose"
    )
    bot.send_message(
        message.chat.id,
        f"Необходимо определить ваш временной пояс, "
        f"выберите на сколько часов смещено ваше время относительно {datetime.datetime.now().strftime('%H:%M')}",
        reply_markup=kb_time_zone
    )


# Начало работы с ботом
@bot.message_handler(commands=["start"])
def start_message(message):
    bot.send_message(
        message.chat.id,
        "Рад снова видеть тебя! Зачем ты пожаловал на этот раз?",
        reply_markup=keyboard_menu
    )


# Справка по работе бота для пользователя
@bot.message_handler(commands=["help"])
def help_message(message):
    bot.send_message(
        message.chat.id,
        "Я создан чтобы ты мог использовать меня как свой ежедневник.\n"
        "Вот список моих возможностей:\n"
        "1. Ты можешь добавлять в меня свои планы, а также просматривать, "
        "удалять и изменять их, когда захочешь.\n"
        "2. На запланированные события ты должен устанавливать приоретет, "
        "чтобы я мог напоминать тебе о них!\n"
        "Наивысший приоретет - 1; "
        "Я буду напоминать тебе об этом событии за день, 4 часа и час до начала.\n"
        "Средний приоретет - 2; "
        "Я буду напоминать тебе об этом событии за день и 4 часа до начала.\n"
        "Слабый приоретет - 3; "
        "Я буду напоминать тебе об этом событии за день до начала.\n"
        "3. Планы, которые уже устарели, автоматический удаляются через несколько дней.\n"
        "Напиши /start чтобы начать работу со мной"
    )


# Интерфейс взаимодействия с сообщениями пользователя
@bot.message_handler(content_types=["text"])
def send_text(message):
    # Берем id пользователя и добавляем его в БД, если его не было
    u_id = message.from_user.id
    users.add_user(
        u_id
    )
    # Вытаскиваем из таблицы дату, выбранную пользователем, его текущее состояние и имя обновляемого объекта.
    # Для дальнейшей обработки
    result_date = users.select_one_cell(
        u_id,
        "result_date"
    )
    user_states = users.select_one_cell(
        u_id,
        "user_states"
    )
    name_upd = users.select_one_cell(
        u_id,
        "name_upd"
    )
    # Определяем смещение времени пользователя относительно сервера
    if users.select_one_cell(u_id, "time_zone") == "":
        time_zone_choose(
            message,
            u_id
        )
    # Проверяем на каком этапе находится пользователь
    if user_states == "name":
        # Устанавливаем имя для создаваемого события
        schedule.set_event_name(
            u_id, result_date,
            message.text.capitalize()
        )
        bot.send_message(
            message.chat.id,
            f"Вы назвали событие: {message.text.capitalize()}. "
            f"Теперь кратко опишите его суть."
        )
        # Устанавливаем статус для создания описания
        users.update_user(
            u_id,
            "user_states",
            "description"
        )
    elif user_states == "description":
        # Устанавливаем описание для создаваемого события
        schedule.set_event_description(
            u_id,
            result_date,
            message.text
        )
        bot.send_message(
            message.chat.id,
            f"Описание вашего события: {message.text}. "
            f"Теперь дадим приоретет вашему событию, "
            f"чтобы узнать больше о них, напишите /help",
            reply_markup=kb_priority
        )
        # Устанивливаем стуткс для выбора приоретета
        users.update_user(
            u_id,
            "user_states",
            "priority"
        )
    elif user_states == "priority":
        # Устанавливаем приоретет для создаваемого события
        # Проверяем корректноть введенных пользователем данных
        if message.text in priority_list:
            schedule.set_event_priority(
                u_id,
                result_date,
                message.text
            )
            bot.send_message(
                message.chat.id,
                f"Выбранный приоретет {message.text}. "
                f"Поздравляю вас с созданием события! Что будем делать теперь?",
                reply_markup=keyboard_menu
            )
            # Событие создано
            # Возвращаем статус пользователя в исходный пустой
            users.update_user(
                u_id,
                "user_states",
                ""
            )
        else:
            bot.send_message(
                message.chat.id,
                "Введено некорректное значение для приоретета, "
                "выберете нужное на клавиатуре",
                reply_markup=kb_priority
            )
    elif user_states == "del_event":
        # Выбираем событие для удаления в выбранный день
        # Проверяем есть ли событие с таким названием в этот день
        if schedule.select_one_cell(
                u_id,
                result_date,
                message.text.capitalize(),
                "name"
        ) is None:
            bot.send_message(
                message.chat.id,
                "Такого события нет в этот день, попробуйте снова"
            )
        else:
            schedule.del_event(
                u_id,
                result_date,
                message.text.capitalize()
            )
            bot.send_message(
                message.chat.id,
                f"Событие {message.text.capitalize()}, "
                f"запланированное на {result_date} успешно удалено! "
                f"Что будем делать теперь?",
                reply_markup=keyboard_menu
            )
            # Возвращаем статус пользователя в исходный пустой
            users.update_user(
                u_id,
                "user_states",
                ""
            )
    elif user_states == "update_event":
        # Выбираем событие для обновления в выбранный день
        # Проверяем есть ли событие с таким названием в этот день -> выбираем что хотим обновить
        name_upd = message.text.capitalize()
        if len(
                schedule.exist_check(
                    u_id,
                    result_date,
                    name_upd
                )
        ) == 0:
            bot.send_message(
                message.chat.id,
                f"Такого события нет в этот день, попробуйте снова"
            )
        else:
            users.update_user(
                u_id,
                "name_upd",
                name_upd
            )
            bot.send_message(
                message.chat.id,
                f"Вы выбрали событие {message.text.capitalize()}, "
                f"Теперь определитесь, что именно вы хотите обновить.",
                reply_markup=keyboard_upd
            )
    elif user_states == "upd_new_name":
        # Устанавливаем новое имя для обновляемого события
        schedule.update_event(
            u_id,
            result_date,
            name_upd,
            "name",
            message.text.capitalize()
        )
        bot.send_message(
            message.chat.id,
            f"Событию {name_upd} присвоено новое имя: {message.text.capitalize()}. "
            f"Что будем делать теперь?",
            reply_markup=keyboard_menu
        )
        # Возвращаем статус пользователя в исходный пустой
        users.update_user(
            u_id,
            "user_states",
            ""
        )
    elif user_states == "upd_new_description":
        # Устанавливаем новое описание для обновляемого события
        schedule.update_event(
            u_id,
            result_date,
            name_upd,
            "description",
            message.text
        )
        bot.send_message(
            message.chat.id,
            f"Событию {name_upd} присвоено новое описание: {message.text}."
            f"Что будем делать теперь?",
            reply_markup=keyboard_menu
        )
        # Возвращаем статус пользователя в исходный пустой
        users.update_user(
            u_id,
            "user_states",
            ""
        )
    elif user_states == "upd_new_priority":
        # Устанавливаем новый приоретет для обновляемого события
        # Проверяем корректноть введенных пользователем данных
        if message.text in priority_list:
            schedule.update_event(
                u_id,
                result_date,
                name_upd,
                "priority",
                message.text
            )
            bot.send_message(
                message.chat.id,
                f"Событию {name_upd} присвоен новый приоретет: {message.text}."
                f"Что будем делать теперь?",
                reply_markup=keyboard_menu
            )
            # Возвращаем статус пользователя в исходный пустой
            users.update_user(
                u_id,
                "user_states",
                ""
            )
        else:
            bot.send_message(
                message.chat.id,
                f"Введено некорректное значения для приоретета, "
                f"выберете нужное на клавиатуре",
                reply_markup=kb_priority
            )
    else:
        # Проверяем что выбрал пользователь из главного меню
        if message.text.lower() == "добавить событие":
            choose_date(
                message
            )
            # Присваемваем пользователю статус "добавление события"
            users.update_user(
                u_id,
                "user_states",
                "add_event"
            )
        elif message.text.lower() == "мои события":
            choose_date(
                message
            )
            # Присваиваем пользователю статус "вывод списка событий"
            users.update_user(
                u_id,
                "user_states",
                "events_list"
            )
        elif message.text.lower() == "удалить событие":
            choose_date(
                message
            )
            # Присваиваем пользователю статус "удаление события"
            users.update_user(
                u_id,
                "user_states",
                "del_event"
            )
        elif message.text.lower() == "обновить событие":
            choose_date(
                message
            )
            # Присваиваем пользователю статус "обновление события"
            users.update_user(
                u_id,
                "user_states",
                "update_event"
            )
        elif message.text.lower() == "обновить временной пояс":
            time_zone_choose(
                message,
                u_id
            )
        else:
            # Если пользователь отправил случайное событие, не определенное в меню, то просим выбрать пункт в меню
            bot.send_message(
                message.chat.id,
                "Приветствую {0} {1}, я бот-ежедневник. Напиши /start, если хочешь начать работу со мной. "
                "А также можешь ввести команду /help, чтобы узнать что я умею".format(
                    message.chat.first_name,
                    message.chat.last_name
                )
            )


# Устанавливаем смещение времени для пользователя
@bot.callback_query_handler(func=lambda c: c.data in time_zone_id)
def cal_choice(c):
    # Добавляем смещение в таблицу для пользователя
    u_id = c.from_user.id
    users.update_user(
        u_id,
        "time_zone",
        c.data
    )
    bot.edit_message_text(
        f"Вы установили смещение {c.data[2:]} ч.",
        c.message.chat.id,
        c.message.message_id
    )


# Интерфейс по выбору даты и для работы с событиями на указанную дату
@bot.callback_query_handler(func=DetailedTelegramCalendar.func())
def cal_date(c):
    # Вытаскиваем из таблицы текущее состояние пользователя и имя обновляемого объекта
    # Для дальнейшей обработки
    u_id = c.from_user.id
    user_states = users.select_one_cell(
        u_id,
        "user_states"
    )
    name_upd = users.select_one_cell(
        u_id,
        "name_upd"
    )
    result_date, key, step = DetailedTelegramCalendar().process(c.data)
    # Проверяем текущий статус пользователя
    if user_states == "events_list":
        # Выводим список событий в указанный день
        if not result_date and key:
            bot.edit_message_text(
                f"За какой {LSTEP[step]} вы хотите просмотреть список событий?",
                c.message.chat.id,
                c.message.message_id,
                reply_markup=key
            )
        elif result_date:
            calendar_ans(
                c,
                u_id,
                result_date,
                key,
                "Это все запланированные события на этот день. Что будем делать теперь?",
                keyboard=keyboard_menu
            )
            # Возвращаем статус пользователя в исходный пустой
            users.update_user(
                u_id,
                "user_states",
                ""
            )
    elif user_states == "add_event":
        # Добавляем событие на указанную дату
        if not result_date and key:
            bot.edit_message_text(
                f"На какой {LSTEP[step]} вы хотите запланировать это событие?",
                c.message.chat.id,
                c.message.message_id,
                reply_markup=key
            )
        elif result_date:
            users.update_user(
                u_id,
                "result_date",
                result_date
            )
            bot.edit_message_text(
                f"Вы выбрали {result_date}. Перейдем к выбору временного промежутка. "
                f"Сперва определимся с временем начала события. Выберете час:",
                c.message.chat.id,
                c.message.message_id,
                reply_markup=kb_hours
            )
            # Присваиваем пользователю статус "выбор времени начала события"
            # Переходим к клавиатурам с выбором времени
            users.update_user(
                u_id,
                "user_states",
                "time_begin"
            )
    elif user_states == "del_event":
        # Удаляем событие в указанную дату
        if not result_date and key:
            bot.edit_message_text(
                f"Выберите {LSTEP[step]}, который соотвутствует удаляемому событию",
                c.message.chat.id,
                c.message.message_id,
                reply_markup=key
            )
        elif result_date:
            calendar_ans(
                c,
                u_id,
                result_date,
                key,
                "Теперь введите имя удаляемого события. Учтите, "
                "если в выбранный день у вас несколько событий с этим именем, то удалятся все."
            )
    elif user_states == "update_event":
        # Обновляем событие в указанную дату
        if not result_date and key:
            bot.edit_message_text(
                f"Выберите {LSTEP[step]}, который соотвутствует обновляему событию",
                c.message.chat.id,
                c.message.message_id,
                reply_markup=key
            )
        elif result_date:
            calendar_ans(
                c,
                u_id,
                result_date,
                key,
                "Теперь введите имя события, которое вы хотите обновить. "
                "Учтите, если в выбранный день у вас несколько событий с этим именем, то обновятся все."
            )
            users.update_user(
                u_id,
                "result_date",
                result_date
            )
    elif user_states == "upd_new_date":
        # Обновляем дату для уже выбранного события для обновления
        if not result_date and key:
            bot.edit_message_text(
                f"Выберите новый {LSTEP[step]} для события",
                c.message.chat.id,
                c.message.message_id,
                reply_markup=key
            )
        elif result_date:
            result_date_old = users.select_one_cell(
                u_id,
                "result_date_old"
            )
            schedule.update_event(
                u_id,
                result_date_old,
                name_upd,
                "date",
                result_date
            )
            bot.send_message(
                c.message.chat.id,
                f"Вы установили новую дату {result_date} для события {name_upd}. Что будем делать теперь?",
                reply_markup=keyboard_menu
            )
            # Возвращаем статус пользователя в исходный пустой
            users.update_user(
                u_id,
                "user_states",
                ""
            )


# Переключение клавиатуры при выборе времени с часов на минуты, сохранение часов в time_event
@bot.callback_query_handler(func=lambda c: c.data in hours_id_list)
def cal_min(c):
    users.update_user(
        c.from_user.id,
        "time_event",
        c.data
    )
    bot.edit_message_text(
        "Выберете минуты:",
        c.message.chat.id,
        c.message.message_id,
        reply_markup=kb_minutes_page1
    )


# Переключение страницы клавиатуры при выборе минут
@bot.callback_query_handler(func=lambda c: c.data == ">>")
def cal_switch_left(c):
    bot.edit_message_text(
        "Выберете минуты:",
        c.message.chat.id,
        c.message.message_id,
        reply_markup=kb_minutes_page2
    )


# Переключение страницы клавиатуры при выборе минут
@bot.callback_query_handler(func=lambda c: c.data == "<<")
def cal_switch_right(c):
    bot.edit_message_text(
        "Выберете минуты:",
        c.message.chat.id,
        c.message.message_id,
        reply_markup=kb_minutes_page1
    )


# Запрос на опеределение времени конца события и создания события в базе данных с указанными датой и временем.
# Запрос на выбор имени события.
@bot.callback_query_handler(func=lambda c: c.data in minutes_list_1 or c.data in minutes_list_2)
def cal_time(c):
    # Вытаскиваем из таблицы текущее состояние пользователя,
    # выбранное время начала, выбранную дату и имя обновляемого объекта
    # Для дальнейшей обработки
    u_id = c.from_user.id
    user_states = users.select_one_cell(
        u_id,
        "user_states"
    )
    time_begin = users.select_one_cell(
        u_id,
        "time_begin"
    )
    result_date = users.select_one_cell(
        u_id,
        "result_date"
    )
    name_upd = users.select_one_cell(
        u_id,
        "name_upd"
    )
    # Добавляем минуты к переменной с часами time_event и обновляем ее
    time_event = users.select_one_cell(
        u_id,
        "time_event"
    ) + c.data
    users.update_user(
        u_id,
        "time_event",
        time_event)
    # Провеляем статус пользователя
    if user_states == "time_begin":
        # Для создаваемого события сохраняем время начала события
        users.update_user(
            u_id,
            "time_begin",
            time_event
        )
        time_begin = time_event
        bot.edit_message_text(
            f"Время начала вашего события: {time_begin}. Желаете ли вы указать время окончания события? "
            f"Если вы выберете 'Нет', то время окончания автоматический станет равным времени начала.",
            c.message.chat.id,
            c.message.message_id,
            reply_markup=kb_choice
        )
    elif user_states == "time_end":
        # Для создаваемого события сохраняем время конца события и добавляем их в БД
        # Проверяем не меньше ли для выбранного события время конца чем время начала
        if int(time_event[:2]) * 60 + int(time_event[3:]) < int(time_begin[:2]) * 60 + int(time_begin[3:]):
            bot.edit_message_text(
                f"Ого! Кажется вы ошиблись, время начала события {time_begin} не может быть позже "
                f"времени конца {time_event}. Давайте попробуем снова определить время конца, выберете час:",
                c.message.chat.id,
                c.message.message_id,
                reply_markup=kb_hours
            )
        else:
            time_end = time_event
            schedule.add_event(
                u_id,
                result_date,
                time_begin,
                time_end
            )
            bot.edit_message_text(
                f"Ваше событие запланировано на {result_date} в период {time_begin}-{time_end}.\n"
                f"Теперь дадим имя вашему событию. Учтите, при обновлении/удалении событий с "
                f"одинаковыми именами и датами все такие события будут обновяться/удаляться.\n"
                f"Поэтому, я советую называть события, запланированные на один день, по-разному.",
                c.message.chat.id,
                c.message.message_id
            )
            # Присваиваем пользователю состояния выбора имени и удаляем уже не нужные переменные
            users.update_user(
                u_id,
                "user_states",
                "name"
            )
            del time_begin, time_end
    elif user_states == "upd_new_time_begin":
        # Обновляем время начала события для выбранного обновляемого события
        # Проверяем не больше ли для выбранного события новое время начала чем время конца
        cur_time_end = schedule.select_one_cell(
            u_id,
            result_date,
            name_upd,
            "time_end"
        )[0]
        if int(time_event[:2]) * 60 + int(time_event[3:]) > int(cur_time_end[:2]) * 60 + int(cur_time_end[3:]):
            bot.edit_message_text(
                f"Ого! Кажется вы ошиблись, время начала события {time_event} не может быть позже "
                f"времени конца {cur_time_end}. Давайте попробуем снова определить время начала, выберете час:",
                c.message.chat.id,
                c.message.message_id,
                reply_markup=kb_hours
            )
        else:
            schedule.update_event(
                u_id,
                result_date,
                name_upd,
                "time_begin",
                time_event
            )
            bot.send_message(
                c.message.chat.id,
                f"Вы установили новое время начала {time_event} для события {name_upd}. "
                f"Что будем делать теперь?",
                reply_markup=keyboard_menu
            )
            # Возвращаем статус пользователя в исходный пустой
            users.update_user(
                u_id,
                "user_states",
                ""
            )
    elif user_states == "upd_new_time_end":
        # Обновляем время конца события для выбранного обновляемого события
        # Проверяем не меньше ли для выбранного события новое время конца чем время начала
        cur_time_beg = schedule.select_one_cell(
            u_id,
            result_date,
            name_upd,
            "time_begin"
        )[0]
        if int(time_event[:2]) * 60 + int(time_event[3:]) < int(cur_time_beg[:2]) * 60 + int(cur_time_beg[3:]):
            bot.edit_message_text(
                f"Ого! Кажется вы ошиблись, время конца события {time_event} не может быть раньше "
                f"времени начала {cur_time_beg}. Давайте попробуем снова определить время конца, выберете час:",
                c.message.chat.id,
                c.message.message_id,
                reply_markup=kb_hours
            )
        else:
            schedule.update_event(
                u_id,
                result_date,
                name_upd,
                "time_end",
                time_event
            )
            bot.send_message(
                c.message.chat.id,
                f"Вы установили новое время конца {time_event} для события {name_upd}. "
                f"Что будем делать теперь?",
                reply_markup=keyboard_menu
            )
            # Возвращаем статус пользователя в исходный пустой
            users.update_user(
                u_id,
                "user_states",
                ""
            )


# Проверяем, хочет ли пользователь установить время конца события
@bot.callback_query_handler(func=lambda c: c.data == "Да" or c.data == "Нет")
def cal_choice(c):
    # Вытаскиваем из таблицы текущие выбранное время начала и выбранную дату
    # Для дальнейшей обработки
    u_id = c.from_user.id
    time_begin = users.select_one_cell(
        u_id,
        "time_begin"
    )
    result_date = users.select_one_cell(
        u_id,
        "result_date"
    )
    if c.data == "Да":
        bot.edit_message_text(
            "Отлично, тогда приступим к выбору времени окончания события."
            "Выберете час:",
            c.message.chat.id,
            c.message.message_id,
            reply_markup=kb_hours
        )
        # Присваиваем пользователю статус "выбор времени конца события"
        users.update_user(
            u_id,
            "user_states",
            "time_end"
        )
    elif c.data == "Нет":
        schedule.add_event(
            u_id,
            result_date,
            time_begin,
            time_begin
        )
        bot.edit_message_text(
            f"Ваше событие запланировано на {result_date} в {time_begin}.\n"
            f"Теперь дадим имя вашему событию. Учтите, при обновлении/удалении событий с "
            f"одинаковыми именами и датами все такие события будут обновяться/удаляться.\n"
            f"Поэтому, я советую называть события, запланированные на один день, по-разному.",
            c.message.chat.id,
            c.message.message_id
        )
        # Присваиваем пользователю состояния выбора имени и удаляем уже не нужные переменные
        users.update_user(
            u_id,
            "user_states",
            "name"
        )


# Функция для обработки запросов на обновление события
@bot.callback_query_handler(func=lambda c: c.data in keyboard_upd_id)
def cal_upd(c):
    # Вытаскиваем из таблицы выбранную дату
    # Для дальнейшей обработки
    u_id = c.from_user.id
    result_date = users.select_one_cell(
        u_id,
        "result_date"
    )
    if c.data == "name":
        # Обновляем имя события -> реакции на text message
        users.update_user(
            u_id,
            "user_states",
            "upd_new_name"
        )
        bot.edit_message_text(
            "Введите новое имя:",
            c.message.chat.id,
            c.message.message_id
        )
    elif c.data == "description":
        # Обновляем описание события -> реакции на text message
        users.update_user(
            u_id,
            "user_states",
            "upd_new_description"
        )
        bot.edit_message_text(
            "Введите новое описание одним сообщением:",
            c.message.chat.id,
            c.message.message_id
        )
    elif c.data == "date":
        # Обновляем дату события -> выбору для в календаре
        users.update_user(
            u_id,
            "user_states",
            "upd_new_date"
        )
        users.update_user(
            u_id,
            "result_date_old",
            result_date
        )
        choose_date(
            c.message
        )
    elif c.data == "time_begin":
        # Обновляем время начала события -> выбору времени для события
        users.update_user(
            u_id,
            "user_states",
            "upd_new_time_begin"
        )
        bot.edit_message_text(
            "Выберете новое значение времени начала события:",
            c.message.chat.id,
            c.message.message_id,
            reply_markup=kb_hours
        )
    elif c.data == "time_end":
        # Обновляем время конца события -> выбору времени для события
        users.update_user(
            u_id,
            "user_states",
            "upd_new_time_end"
        )
        bot.edit_message_text(
            "Выберете новое значение времени конца события:",
            c.message.chat.id,
            c.message.message_id,
            reply_markup=kb_hours
        )
    elif c.data == "priority":
        # Обновляем приоретет события -> выбору приоретета для события
        users.update_user(
            u_id,
            "user_states",
            "upd_new_priority"
        )
        bot.edit_message_text(
            "Вы выбрали изменение приоретета",
            c.message.chat.id,
            c.message.message_id
        )
        bot.send_message(
            c.message.chat.id,
            "Выберете новое значение приоретета:",
            reply_markup=kb_priority
        )


# Блок функций для уведомления пользователя о событии
# Реализуем функцию, которая будет удалять все события раньше текущего дня
# Ставим таймер, чтобы процедура повторялась каждые 3 дня
def del_thread():
    threading.Timer(
        259200,
        del_thread
    ).start()
    schedule.del_old_events(
        datetime.datetime.now().date() - datetime.timedelta(days=1)
    )


# Функция для уведомления пользователя
def events_list_notif(events_list, text):
    for event in events_list:
        u_id, nam, time_b, time_e = event
        bot.send_message(
            u_id,
            f"{text} у вас запланировано событие {nam} в {time_b}-{time_e}"
        )


# Функция для проверки и вытаскивания событий, который начнуться в промежутке h_l:m_l-h_h:m_h
# + текущее время к этим пределам
def notif_check(h_l, m_l, h_h, m_h, prio, mess):
    users_list = users.user_tz_list()
    for user in users_list:
        u_id, tz = user
        date_time = (
                datetime.datetime.now() +
                datetime.timedelta(hours=int(tz[2:])) +
                datetime.timedelta(hours=h_l, minutes=m_l)
        ).strftime("%Y-%m-%d %H:%M")
        date = list(date_time.split(" "))[0]
        time_low_lim = list(date_time.split(" "))[1]
        time_high_lim = (datetime.datetime.now() +
                         datetime.timedelta(hours=int(tz[2:])) +
                         datetime.timedelta(hours=h_h, minutes=m_h)
                         ).strftime("%H:%M")
        events_list = schedule.notification_2(
            u_id,
            date,
            time_low_lim,
            time_high_lim,
            prio
        )
        if events_list is not None:
            events_list_notif(
                events_list,
                mess
            )


# Функция напоминающая о событиях за день до начала
def event_notific_first():
    threading.Timer(
        86400,
        event_notific_first
    ).start()
    events_list = schedule.notification_1(
        datetime.datetime.now().date() + datetime.timedelta(days=1)
    )
    if events_list is not None:
        events_list_notif(
            events_list,
            "На завтра"
        )


# Функция напоминающая о событиях за 4 часа до начала
def event_notific_second():
    threading.Timer(
        3600,
        event_notific_second
    ).start()
    notif_check(3, 0, 5, 0, "priority != 3", "Примерно через 4 часа")


# Функция напоминающая о событиях за час до начала
def event_notific_tird():
    threading.Timer(
        600,
        event_notific_tird
    ).start()
    notif_check(0, 45, 1, 15, "priority = 1", "Примерно через час")


if __name__ == "__main__":
    event_notific_first()
    event_notific_second()
    event_notific_tird()
    del_thread()
    bot.polling()
