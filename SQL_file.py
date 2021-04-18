import sqlite3


class SQLighter:
    def __init__(self, database):
        self.connection = sqlite3.connect(
            database,
            check_same_thread=False
        )
        self.cursor = self.connection.cursor()

    def select_all_events(self, user_id, date):
        """Получаем все события в указанный день"""
        with self.connection:
            return self.cursor.execute(
                "SELECT time_begin, time_end, name, description, priority FROM personal_schedule "
                "WHERE (user_id, date) = (?,?)"
                "ORDER BY time_begin",
                (user_id, date,)
            ).fetchall()

    def select_one_cell(self, user_id, date, name, column):
        """Получаем конкретный атрибут определенного события в указанный день"""
        with self.connection:
            return self.cursor.execute(
                "SELECT {} FROM personal_schedule WHERE (user_id, date, name) = (?,?,?)".format(column),
                (user_id, date, name,)
            ).fetchone()

    def exist_check(self, user_id, date, name):
        """Проверяем есть ли события с указанным именем и датой"""
        with self.connection:
            return self.cursor.execute(
                "SELECT name FROM personal_schedule WHERE (user_id, date, name) = (?,?,?)",
                (user_id, date, name,)
            ).fetchall()

    def add_event(self, user_id, date, time_begin, time_end, name="-", description="-", priority="-"):
        """Добавляем новое событие в БД"""
        with self.connection:
            self.cursor.execute(
                "INSERT INTO personal_schedule "
                "(user_id, date, time_begin, time_end, name, description, priority) "
                "VALUES (?,?,?,?,?,?,?)",
                (user_id, date, time_begin, time_end, name, description, priority)
            )
            self.connection.commit()

    def del_event(self, user_id, date, name):
        """Удаляем определенное событие из БД в указанный день"""
        with self.connection:
            self.cursor.execute(
                "DELETE FROM personal_schedule WHERE (user_id, date, name) = (?,?,?)",
                (user_id, date, name,)
            )
            self.connection.commit()

    def update_event(self, user_id, date, name, column, value):
        """Обновляем атрибут определенного события в БД в указанный день"""
        with self.connection:
            self.cursor.execute(
                "UPDATE personal_schedule SET {} = ? WHERE (user_id, date, name) = (?,?,?)".format(column),
                (value, user_id, date, name,)
            )
            self.connection.commit()

    def set_event_name(self, user_id, date, value, name="-", description="-", priority="-"):
        """Устанавливаем имя для созданного события в БД"""
        with self.connection:
            self.cursor.execute(
                "UPDATE personal_schedule SET name = ? "
                "WHERE (user_id, date, name, description, priority) = (?,?,?,?,?)",
                (value, user_id, date, name, description, priority,)
            )
            self.connection.commit()

    def set_event_description(self, user_id, date, value, description="-", priority="-"):
        """Устанавливаем описание для созданного события в БД"""
        with self.connection:
            self.cursor.execute(
                "UPDATE personal_schedule SET description = ? "
                "WHERE (user_id, date, description, priority) = (?,?,?,?)",
                (value, user_id, date, description, priority,)
            )
            self.connection.commit()

    def set_event_priority(self, user_id, date, value, priority="-"):
        """Устанавливаем приоретет для созданного события в БД"""
        with self.connection:
            self.cursor.execute(
                "UPDATE personal_schedule SET priority = ? "
                "WHERE (user_id, date, priority) = (?,?,?)",
                (value, user_id, date, priority,)
            )
            self.connection.commit()

    def del_old_events(self, date):
        """Удаляем устаревшие события в БД"""
        with self.connection:
            self.cursor.execute(
                "DELETE FROM personal_schedule WHERE date < ?",
                (date,)
            )
            self.connection.commit()

    def notification_1(self, date):
        """Выбираем завтрашние события для уведомлений"""
        with self.connection:
            return self.cursor.execute(
                "SELECT user_id, name, time_begin, time_end FROM personal_schedule "
                "WHERE date = ? ORDER BY time_begin",
                (date,)
            ).fetchall()

    def notification_2(self, user_id, date, time_1, time_2, priority):
        """Выбираем события через несколько часов для уведомлений"""
        with self.connection:
            return self.cursor.execute(
                "SELECT user_id, name, time_begin, time_end FROM personal_schedule "
                "WHERE {} AND user_id = ? AND date = ? "
                "AND time_begin >= ? AND time_begin <= ? "
                "ORDER BY time_begin".format(priority),
                (user_id, date, time_1, time_2,)
            ).fetchall()

    def close(self):
        """Закрываем текущее соединение с БД"""
        self.connection.close()
