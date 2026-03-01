import asyncio
import json

from aiogram import BaseMiddleware
from aiogram.enums import ChatAction
from aiogram.types import TelegramObject, Message, CallbackQuery
from pathlib import Path

from Services.Reader import ReaderCache


class DataMiddleware(BaseMiddleware):
    BASE_PATH = Path("Users")

    async def __call__(self, handler, event: TelegramObject, data: dict):
        bot = data.get("bot")
        user_id = None
        username = None


        # Если это сообщение
        if event.message:
            user = event.message.from_user
            user_id = user.id
            username = user.username
            first_name = user.first_name
            last_name = user.last_name
            chat_id = event.message.chat.id

        # Если это callback
        elif event.callback_query:
            user = event.callback_query.from_user
            user_id = user.id
            username = user.username
            first_name = user.first_name
            last_name = user.last_name
            chat_id = event.callback_query.message.chat.id

        if user_id:
            reader = ReaderCache.get_reader(user_id)

            data["user_id"] = user_id
            data["reader"] = reader

            # создаем папку пользователя
            user_folder = self.BASE_PATH / str(user_id)
            user_folder.mkdir(parents=True, exist_ok=True)

            user_json_path = user_folder / "user.json"
            user_data = {
                "username": username,
            }
            # если файла нет — создаем
            if not user_json_path.exists():
                with open(user_json_path, "w", encoding="utf-8") as f:
                    json.dump(user_data, f, ensure_ascii=False, indent=4)


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