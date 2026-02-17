from apscheduler.schedulers.asyncio import AsyncIOScheduler
from services.user_manager import UserManager

scheduler = AsyncIOScheduler()


class SchedulerService:

    @classmethod
    def restore_all_jobs(cls, sender_service):
        users = UserManager.get_all_users()

        if not users:
            print("No users to restore")
            return

        for user_id in users:
            time_str = UserManager.get_time(user_id)
            if not time_str:
                continue

            cls.create_user_job(sender_service, user_id, time_str)

    @classmethod
    def create_user_job(cls, sender_service, user_id, time):
        hour, minute = cls._parse_time(time)
        job_id = cls._job_id(user_id)

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

    @staticmethod
    def _parse_time(time_str: str):
        hour, minute = map(int, time_str.split(":"))
        return hour, minute

    @staticmethod
    def _job_id(user_id: int):
        return f"user_{user_id}"
