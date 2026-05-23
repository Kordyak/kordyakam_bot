import asyncio
import contextlib

from aiogram import BaseMiddleware
from aiogram.enums import ChatAction
from aiogram.types import TelegramObject, CallbackQuery

from SQL.DB_library import DB_library
from Services.PrefetchManager import PrefetchManager
from Services.Reader import Reader
from typing import Callable, Awaitable, Dict, Any

from config import Config, load_config


class MiddlewareUsers(BaseMiddleware):
    async def __call__(self, handler, event: TelegramObject, data: dict):
        # bot = data.get("bot")
        user_id = event.from_user.id
        username = event.from_user.username
        username = f"@{username}" if username else None
        lang = event.from_user.language_code

        db = DB_library()
        db.save_last_contact(user_id)
        db.get_create_user(user_id, username)

        reader = await asyncio.to_thread(Reader, user_id, db, lang)
        data["reader"] = reader

        data["db"] = db

        return await handler(event, data)



ADMIN_ID = load_config().tg_bot.admin_ids
class MiddlewareAdmin(BaseMiddleware):
    async def __call__(
            self,
            handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: dict
    )->Any:
        user_id = event.from_user.id
        if user_id in ADMIN_ID:
            return await handler(event, data)
