import asyncio
from aiogram import BaseMiddleware
from aiogram.enums import ChatAction
from aiogram.types import TelegramObject

from SQL.RR_sql import ReadRepository, PATH_READ_DB
from Services.Reader import Reader


class Middleware_typing(BaseMiddleware):
    async def __call__(self, handler, event: TelegramObject, data: dict):
        bot = data.get("bot")
        chat_id = None
        user_id = None

        if event.message:
            user_id = event.message.from_user.id
        elif event.callback_query:
            user_id = event.callback_query.from_user.id

        if user_id:
            data["user_id"] = user_id

            reader = Reader(user_id)

            data["reader"] = reader

        rr = ReadRepository()
        data["rr"] = rr

        if event.message:
            chat_id = event.message.chat.id
        elif event.callback_query:
            chat_id = event.callback_query.message.chat.id

        typing_task = asyncio.create_task(self._typing_loop(bot, chat_id))

        try:
            return await handler(event, data)
        finally:
            if typing_task:
                typing_task.cancel()

    async def _typing_loop(self, bot, chat_id: int):
        try:
            while True:
                await bot.send_chat_action(chat_id, ChatAction.TYPING)
                await asyncio.sleep(4)
        except asyncio.CancelledError:
            pass
