from apscheduler.schedulers.asyncio import AsyncIOScheduler
from Services.StateUser import StateUser

scheduler = AsyncIOScheduler()


class Scheduler:

    @classmethod
    def restore_all_jobs(cls, sender_service):
        users = StateUser.get_all_users()

        if not users:
            print("No users to restore")
            return

        for user_id in users:
            time_str = StateUser.get_time(user_id)
            if not time_str:
                continue

            cls.create_user_job(sender_service, user_id, time_str)

    @classmethod
    def create_user_job(cls, sender_service, user_id, time):
        hour, minute = map(int, time.split(":"))
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


