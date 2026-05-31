import asyncio

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, CallbackQuery
from SQL.DB_library import DB_library
from Services.Reader import Reader
from typing import Callable, Awaitable, Dict, Any
from config import load_config

ADMIN_ID = int(load_config().tg_bot.admin_id)

class MiddlewareUsers(BaseMiddleware):
    async def __call__(self, handler, event: TelegramObject, data: dict):
        user_id = event.from_user.id
        username = event.from_user.username
        username = f"@{username}" if username else None
        lang = event.from_user.language_code

        db, reader, is_new_user = await asyncio.to_thread(self._setup_user, user_id, username, lang)

        if is_new_user:
            bot = data.get("bot")
            await bot.send_message(ADMIN_ID, f"🆕 Новый пользователь: {username}, id: {user_id}")

        data["reader"] = reader
        data["db"] = db
        return await handler(event, data)

    @staticmethod
    def _setup_user(user_id, username, lang):
        db = DB_library()
        is_new_user = db.save_user(user_id, username)
        reader = Reader(user_id, db, lang)
        return db, reader, is_new_user




class MiddlewareAdmin(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: dict
    )->Any:
        user_id = event.from_user.id
        if user_id == ADMIN_ID:
            return await handler(event, data)
