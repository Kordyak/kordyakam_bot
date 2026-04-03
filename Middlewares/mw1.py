import asyncio
from aiogram import BaseMiddleware
from aiogram.enums import ChatAction
from aiogram.types import TelegramObject, Message, CallbackQuery

from SQL.RR_sql import ReadRepository, PATH_READ_DB
from Services.Reader import Reader
from typing import Callable, Awaitable, Dict, Any


class Middleware_typing(BaseMiddleware):
    async def __call__(self, handler, event: TelegramObject, data: dict):
        bot = data.get("bot")
        user_id = event.from_user.id
        user_name = event.from_user.full_name

        data["user_id"] = user_id
        data["user_name"] = user_name
        reader = Reader(user_id)
        data["reader"] = reader
        rr = ReadRepository()
        rr.get_or_create_user(user_id,user_name)
        data["rr"] = rr

        if isinstance(event, CallbackQuery):
            chat_id = event.message.chat.id
        else:
            chat_id = event.chat.id
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



ADMIN_ID = 995657021

class Middleware_access_maintenenace(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: dict
    )->Any:
        user_id = event.from_user.id

        # если не админ — просто не пускаем дальше
        if user_id != ADMIN_ID:
            return  # блокируем обработку

        # если админ — прокидываем дальше
        return await handler(event, data)