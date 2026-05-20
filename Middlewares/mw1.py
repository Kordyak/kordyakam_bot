import asyncio
import contextlib

from aiogram import BaseMiddleware
from aiogram.enums import ChatAction
from aiogram.types import TelegramObject, CallbackQuery

from SQL.DB_library import DB_library
from Services.Reader import Reader
from typing import Callable, Awaitable, Dict, Any


class MiddlewareUsers(BaseMiddleware):
    async def __call__(self, handler, event: TelegramObject, data: dict):
        bot = data.get("bot")
        user_id = event.from_user.id
        username = event.from_user.username
        username = f"@{username}" if username else None
        lang = event.from_user.language_code

        db = DB_library()
        db.save_last_contact(user_id)

        if isinstance(event, CallbackQuery):
            chat_id = event.message.chat.id
        else:
            chat_id = event.chat.id

        typing_task = None
        if chat_id:
            typing_task = asyncio.create_task(self._typing_loop(bot, chat_id))

        reader = Reader(user_id, username, lang)
        data["reader"] = reader

        try:
            return await handler(event, data)
        finally:
            if typing_task:
                typing_task.cancel()
                with contextlib.suppress(asyncio.CancelledError):
                    await typing_task

    async def _typing_loop(self, bot, chat_id: int):
        try:
            while True:
                await bot.send_chat_action(chat_id, ChatAction.TYPING)
                await asyncio.sleep(4)
        except asyncio.CancelledError:
            pass



ADMIN_ID = 995657021
class MiddlewareAdmin(BaseMiddleware):
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