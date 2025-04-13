import sqlite3


class BusStopDAO:
    def __init__(self, db_path: str):
        self.db_path = db_path

    def get_connection(self) -> sqlite3.Connection:
        """
        Создает и возвращает асинхронное соединение с базой данных.
        """
        return sqlite3.connect(self.db_path)

    def get_all_stops(self):
        with self.get_connection() as conn:
            cursor = conn.execute("SELECT stop_name FROM stops")
            result = cursor.fetchall()
            return result

    def get_stop_link(self, stop_name: str) -> str | None:
        """
        Возвращает ссылку (stop_url) для остановки с указанным именем.
        Если остановка не найдена, возвращает None.
        """
        select_sql = "SELECT stop_url FROM stops WHERE stop_name = ?;"
        with self.get_connection() as conn:
            cursor = conn.execute(select_sql, (stop_name,))
            row = cursor.fetchone()
            return row[0] if row else None
