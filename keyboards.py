# Импортируем модуль для создания бота
import telebot
# Импортируем модуль для создания клавиатур
from keyboa import keyboa_maker, keyboa_combiner

# Добавляем клавиатуру - меню
keyboard_menu = telebot.types.ReplyKeyboardMarkup(
    True,
    True
)
keyboard_menu.row("Добавить событие", "Удалить событие")
keyboard_menu.row("Мои события", "Обновить событие")
keyboard_menu.row("Обновить временной пояс")
# Добавляем клавиатуру выбора пунка, которых необходимо обновить
keyboard_upd_list = [("Дата", "date"), ("Время начала", "time_begin"), ("Время конца", "time_end"),
                     ("Имя", "name"), ("Описание", "description"), ("Приоретет", "priority")]
keyboard_upd_id = ["date", "time_begin", "time_end", "name", "description", "priority"]
keyboard_upd = keyboa_maker(
    keyboard_upd_list,
    items_in_row=3
)
# Добавляем клавиатуру для выбора часов и ее индификаторы:
hours_list = []
hours_id_list = [str(i).zfill(2) + ":" for i in range(24)]
for i in range(24):
    hours_list.append(
        {str(i).zfill(2): f"{str(i).zfill(2)}:"}
    )
kb_hours = keyboa_maker(
    hours_list,
    items_in_row=4
)
# Добавляем клавиатуру для выбора минут и ее индификаторы (клавиатуру делим на 2 страницы):
minutes_list_1 = list(
    map(
        lambda x: str(x).zfill(2),
        range(30)
    )
)
minutes_list_2 = list(
    map(
        lambda x: str(x).zfill(2),
        range(30, 60)
    )
)
switch_list_1 = [">>"]
switch_list_2 = ["<<"]
kb_minutes_1 = keyboa_maker(
    minutes_list_1,
    copy_text_to_callback=True,
    items_in_row=5
)
kb_minutes_2 = keyboa_maker(
    minutes_list_2,
    copy_text_to_callback=True,
    items_in_row=5
)
kb_switch_1 = keyboa_maker(
    switch_list_1,
    copy_text_to_callback=True,
    items_in_row=5
)
kb_switch_2 = keyboa_maker(
    switch_list_2,
    copy_text_to_callback=True,
    items_in_row=5
)
kb_minutes_page1 = keyboa_combiner(
    (kb_minutes_1, kb_switch_1)
)
kb_minutes_page2 = keyboa_combiner(
    (kb_minutes_2, kb_switch_2)
)
# Добавляем клавиатуру выбора приорета события
kb_priority = telebot.types.ReplyKeyboardMarkup(
    True,
    True
)
priority_list = ["1", "2", "3"]
kb_priority.row("1", "2", "3")
# Добавляем клавиатуру для выбора между указанием времени конца и отсутствием указания.
kb_choice = keyboa_maker(
    ["Да", "Нет"],
    copy_text_to_callback=True,
)
# Добавляем клавиатуру выбора смещения часового пояса
time_zone_list = []
time_zone_id = ["zn" + str(i) for i in range(-12,13,1)]
for i in range(-12,13,1):
    time_zone_list.append(
        {str(i): f"zn{str(i)}"}
    )
kb_time_zone = keyboa_maker(
    time_zone_list,
    items_in_row=4
)