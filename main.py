import asyncio
import logging
import re

from telethon import events, TelegramClient

from datetime import datetime, timedelta

from aiogram import Dispatcher, Bot, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import Message

from config import *
from services.service import check_word, send_message_ia, send_audio_message
from handlers import handler_admin

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    style='{',
                    format='#[{asctime}] #{levelname} | {name} | : "{message}"')
logger.info(f'Start bot!!!')

config: Config = load_config()

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

client = TelegramClient('kord2', config.client.api_id, config.client.api_hash)
client.start()

bot = Bot(token=config.tg_bot.token,
          default=DefaultBotProperties(parse_mode='MARKDOWN'))
dp = Dispatcher()
dp.include_router(handler_admin.router)

loop.create_task(dp.start_polling(bot))
dp['client'] = client


@client.on(events.NewMessage(chats=channels_id))
async def handler(event):
    key: str = check_word(event.message.text, key_words)
    if key:
        await send_message_ia(bot, event.message, key)


@dp.message(F.text, Command('audio'))
async def handler(message: Message):
        await send_audio_message(message.reply_to_message)



client.run_until_disconnected()

# if __name__ == '__main__':
#     client.run_until_disconnected()


# async def my_channels():
#     dialogs = await client.get_dialogs()
#     for dialog in dialogs:
#         if dialog.is_channel:
#                 channels_id.append(dialog.id)
#             channels_id.append(f"https://t.me/{dialog.entity.username}")
#             print(f"{dialog.id} | {dialog.entity.username} | {dialog.id}")
#
# loop.create_task(my_channels())