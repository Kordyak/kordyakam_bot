from apscheduler.schedulers.asyncio import AsyncIOScheduler

from SQL.RR import ReadRepository

scheduler = AsyncIOScheduler()


class Scheduler:
    """
    Планировщик ежедневных задач пользователей через ReadRepository.
    Все взаимодействия с БД идут через методы ReadRepository.
    """

    @classmethod
    def restore_all_jobs(cls, sender_service, rr: ReadRepository):
        """Восстанавливает все задачи для пользователей из ReadRepository"""
        users = rr.list_users_with_time()
        if not users:
            print("No users to restore")
            return

        for user in users:
            cls.create_user_job(sender_service, user["user_id"], user["daily_time"])

    @classmethod
    def create_user_job(cls, sender_service, user_id: int, time_str: str):
        """Создаёт или обновляет задачу APScheduler для пользователя"""
        hour, minute = map(int, time_str.split(":"))
        job_id = f"user_{user_id}"

        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)

        scheduler.add_job(
            sender_service.send_daily_text,
            trigger="cron",
            hour=hour,
            minute=minute,
            args=[user_id],
            id=job_id,
            replace_existing=True,
        )

    @classmethod
    def add_user_job(cls, sender_service, rr, user_id: int, time_str: str):
        """
        Добавляет или обновляет задачу для пользователя и сохраняет время в БД
        """
        # Сохраняем/обновляем время в базе
        rr.save_time(user_id, time_str)
        # Создаём задачу в APScheduler
        cls.create_user_job(sender_service, user_id, time_str)

    @classmethod
    def remove_user_job(cls, user_id: int, rr=None):
        """
        Удаляет задачу пользователя из APScheduler.
        Если передан rr, можно также очистить daily_time в базе.
        """
        job_id = f"user_{user_id}"
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)

        if rr:
            rr.save_time(user_id, None)