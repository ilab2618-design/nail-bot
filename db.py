import aiosqlite


class Database:
    def __init__(self, path: str):
        self.path = path
        self.db = None

    async def connect(self):
        self.db = await aiosqlite.connect(self.path)
        self.db.row_factory = aiosqlite.Row

    async def init(self):
        await self.connect()

        await self.db.execute("""
        CREATE TABLE IF NOT EXISTS work_days (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            work_date TEXT UNIQUE,
            is_closed INTEGER DEFAULT 0
        )
        """)

        await self.db.execute("""
        CREATE TABLE IF NOT EXISTS time_slots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            work_day_id INTEGER,
            slot_time TEXT,
            is_booked INTEGER DEFAULT 0
        )
        """)

        await self.db.execute("""
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            client_name TEXT,
            phone TEXT,
            slot_id INTEGER,
            status TEXT,
            reminder_job_id TEXT
        )
        """)

        await self.db.commit()

    async def execute(self, query, params=()):
        await self.db.execute(query, params)

    async def fetchone(self, query, params=()):
        cursor = await self.db.execute(query, params)
        return await cursor.fetchone()

    async def fetchall(self, query, params=()):
        cursor = await self.db.execute(query, params)
        return await cursor.fetchall()

    async def commit(self):
        await self.db.commit()

    async def get_active_appointment_by_user(self, user_id: int):
        return await self.fetchone(
            """
            SELECT a.id, wd.work_date, ts.slot_time
            FROM appointments a
            JOIN time_slots ts ON ts.id = a.slot_id
            JOIN work_days wd ON wd.id = ts.work_day_id
            WHERE a.user_id = ? AND a.status = 'booked'
            """,
            (user_id,)
        )

    async def get_available_dates_in_range(self, start_date: str, end_date: str):
        rows = await self.fetchall(
            """
            SELECT DISTINCT wd.work_date
            FROM work_days wd
            JOIN time_slots ts ON ts.work_day_id = wd.id
            WHERE wd.is_closed = 0
              AND ts.is_booked = 0
              AND wd.work_date BETWEEN ? AND ?
            ORDER BY wd.work_date
            """,
            (start_date, end_date)
        )
        return [row["work_date"] for row in rows]

    async def get_free_slots_by_date(self, work_date: str):
        return await self.fetchall(
            """
            SELECT ts.id, ts.slot_time
            FROM time_slots ts
            JOIN work_days wd ON wd.id = ts.work_day_id
            WHERE wd.work_date = ?
              AND wd.is_closed = 0
              AND ts.is_booked = 0
            ORDER BY ts.slot_time
            """,
            (work_date,)
        )

    async def get_available_slots_by_date(self, work_date: str):
        return await self.get_free_slots_by_date(work_date)