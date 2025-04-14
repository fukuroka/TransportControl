import aiosqlite


class BusStopDAO:
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn: aiosqlite.Connection | None = None

    async def connect(self):
        """
        Устанавливает асинхронное соединение с базой данных.
        Вызывать один раз при запуске приложения.
        """
        self.conn = await aiosqlite.connect(self.db_path)
        self.conn.row_factory = aiosqlite.Row  # Чтобы получать словари, если нужно

    async def close(self):
        """
        Закрывает соединение с базой данных.
        Вызывать при завершении работы приложения.
        """
        if self.conn:
            await self.conn.close()

    async def get_all_stops(self) -> list[str]:
        """
        Возвращает список всех остановок.
        """
        cursor = await self.conn.execute("SELECT stop_name FROM stops")
        rows = await cursor.fetchall()
        return [row[0] for row in rows]

    async def get_stop_link(self, stop_name: str) -> str | None:
        """
        Возвращает ссылку (stop_url) для указанной остановки.
        """
        cursor = await self.conn.execute(
            "SELECT stop_url FROM stops WHERE stop_name = ?;", (stop_name,)
        )
        row = await cursor.fetchone()
        return row[0] if row else None
