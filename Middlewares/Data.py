from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from pathlib import Path

from Services.Reader import ReaderCache


class DataMiddleware(BaseMiddleware):
    BASE_PATH = Path("Users")

    async def __call__(self, handler, event: TelegramObject, data: dict):

        user_id = None

        # Если это сообщение
        if event.message:
            user_id = event.message.from_user.id

        # Если это callback
        elif event.callback_query:
            user_id = event.callback_query.from_user.id

        if user_id:
            reader = ReaderCache.get_reader(user_id)
            data["user_id"] = user_id
            data["reader"] = reader

            # создаем папку пользователя, если не существует
            user_folder = self.BASE_PATH / str(user_id)
            user_folder.mkdir(parents=True, exist_ok=True)

        return await handler(event, data)
