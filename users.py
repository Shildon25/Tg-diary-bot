import sqlite3

# Создаем класс для работы с несколькими пользователями
class Users_list():
    def __init__(self, database):
        self.connection = sqlite3.connect(
            database,
            check_same_thread=False
        )
        self.cursor = self.connection.cursor()

    def user_check(self, user_id):
        """Проверяем существует ли пользователь"""
        with self.connection:
            return self.cursor.execute(
                "SELECT user_id FROM users WHERE user_id = ?",
                (user_id, )
            ).fetchone()

    def add_user(self, user_id, time_zone="", user_states="", result_date="", name_upd="", result_date_old="", time_event="", time_begin=""):
        """Добавляем нового пользователя в БД"""
        if self.user_check(user_id) is None:
            with self.connection:
                self.cursor.execute(
                    "INSERT INTO users (user_id, time_zone, user_states, result_date, name_upd, "
                    "result_date_old, time_event, time_begin) VALUES (?,?,?,?,?,?,?,?)",
                    (user_id, time_zone, user_states, result_date, name_upd, result_date_old, time_event, time_begin, )
                )
                self.connection.commit()

    def check_user_states(self, user_id):
        """Проверяем текущий статус пользователя"""
        with self.connection:
            return self.cursor.execute(
                "SELECT user_states FROM users WHERE user_id = ?",
                (user_id, )
            ).fetchone()[0]

    def user_tz_list(self):
        """Получаем список пользователей с их часовыми поясами"""
        with self.connection:
            return self.cursor.execute(
                "SELECT user_id, time_zone FROM users"
            ).fetchall()

    def select_one_cell(self, user_id, column):
        """Получаем конкретный атрибут определенного пользователя"""
        with self.connection:
            return self.cursor.execute(
                "SELECT {} FROM users WHERE user_id = ?".format(column),
                (user_id,)
            ).fetchone()[0]

    def update_user(self, user_id, column, value):
        """Обновляем атрибут определенного пользователя в БД в указанный день"""
        with self.connection:
            self.cursor.execute(
                "UPDATE users SET {} = ? WHERE user_id = ?".format(column),
                (value, user_id,)
            )
            self.connection.commit()

    def close(self):
        """Закрываем текущее соединение с БД"""
        self.connection.close()