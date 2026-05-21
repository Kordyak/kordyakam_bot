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
        users = db.get_users_to_send(now)

        for user in users:
            user_id = user["user_id"]
            reader = Reader(user_id, db)
            if reader.book_title:
                await self.sender.send_chunk(reader)

            if reader.paragraph_indx == reader.total_paragraphs:
                db.remove_current_book(user_id)