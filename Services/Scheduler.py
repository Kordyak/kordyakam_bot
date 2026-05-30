import asyncio
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from SQL.DB_library import DB_library
from Services.Reader import Reader
from Services.Sender import Sender

scheduler = AsyncIOScheduler()

class Scheduler:
    """
    Планировщик ежедневных задач пользователей через DB_library.
    Все взаимодействия с БД идут через методы DB_library.
    """
    def __init__(self, sender: Sender):
        self.sender = sender
        scheduler.add_job(
            self.send_all_users,
            trigger="interval",
            minutes=1,
        )

    async def send_all_users(self):
        db = DB_library()
        now = datetime.now()
        users = db.get_users_by_time(now)

        tasks = []
        for user in users:
            if user['current_book_id']:
                tasks.append(self._send_to_user(user["user_id"], db))

        await asyncio.gather(*tasks)  # параллельно, не блокируем

    async def _send_to_user(self, user_id: int, db):
        reader = await asyncio.to_thread(Reader, user_id, db)  # ← в отдельный поток
        await self.sender.send_chunk(reader)
        if reader.paragraph_indx == reader.total_paragraphs:
            db.remove_current_book(user_id)

            # user_id = user["user_id"]
            # reader = Reader(user_id, db)
            # if reader.book_title:
            #     await self.sender.send_chunk(reader)
            #
            # if reader.paragraph_indx == reader.total_paragraphs:
            #     db.remove_current_book(user_id)