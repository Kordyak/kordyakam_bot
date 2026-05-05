from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from sympy.physics.units import minutes

from SQL.DB_library import DB_library
from Services.Reader import Sender

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
        rr = DB_library()
        now = datetime.now()
        users = rr.get_users_to_send(now)
        for user in users:
            await self.sender.send_chunk(user["user_id"])


    # @classmethod
    # def restore_all_jobs(cls, sender_service, db: DB_library):
    #     """Восстанавливает все задачи для пользователей из DB_library"""
    #     users = db.list_users_with_time()
    #     if not users:
    #         print("No users to restore")
    #         return
    #
    #     for user in users:
    #         cls.create_user_job(sender_service, user["user_id"], user["daily_time"])
    #
    # @classmethod
    # def create_user_job(cls, sender_service, user_id: int, time_str: str):
    #     """Создаёт или обновляет задачу APScheduler для пользователя"""
    #     hour, minute = map(int, time_str.split(":"))
    #     job_id = f"user_{user_id}"
    #
    #     if scheduler.get_job(job_id):
    #         scheduler.remove_job(job_id)
    #
    #     scheduler.add_job(
    #         sender_service.send_daily_text,
    #         trigger="cron",
    #         hour=hour,
    #         minute=minute,
    #         args=[user_id],
    #         id=job_id,
    #         replace_existing=True,
    #     )
    #
