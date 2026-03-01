import asyncio

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
        chat_id = None
        username = None

        # Если это сообщение
        if event.message:
            user_id = event.message.from_user.id
            username = event.message.from_user.username
            chat_id = event.message.chat.id

        # Если это callback
        elif event.callback_query:
            user_id = event.callback_query.from_user.id
            username = event.callback_query.from_user.username
            chat_id = event.callback_query.message.chat.id

        if user_id:
            reader = ReaderCache.get_reader(user_id)
            data["user_id"] = user_id
            data["reader"] = reader

            old_folder = self.BASE_PATH / str(user_id)
            new_folder = self.BASE_PATH / f"{user_id}_{username}"

            # если существует старая папка и нет новой — переименовываем
            if old_folder.exists() and not new_folder.exists():
                old_folder.rename(new_folder)

            # создаём новую (если ещё не существует)
            new_folder.mkdir(parents=True, exist_ok=True)

        typing_task = asyncio.create_task(
            self._typing_loop(bot, chat_id)
        )



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