from datetime import datetime

from apscheduler.schedulers.asyncio import AsyncIOScheduler

scheduler = AsyncIOScheduler()




class SchedulerService:

    @classmethod
    def create_user_job(cls, user_id, time):

        hour, minute = map(int, time.split(":"))

        scheduler.add_job(
            ReaderService.send_next_chunk,
            "cron",
            hour=hour,
            minute=minute,
            args=[user_id],
            id=f"user_{user_id}"
        )




async def check_users(bot):

    users = UserRegistry.load()

    now = datetime.now().strftime("%H:%M")

    for user_id, data in users.items():

        if data["time"] == now:

            reader = ReaderService.get_reader(user_id)

            await send_daily_text(bot, reader)