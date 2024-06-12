import asyncio
import logging

from telethon import events, TelegramClient

from datetime import datetime, timedelta

from aiogram import Dispatcher, Bot
from aiogram.client.default import DefaultBotProperties
from aiogram import filters, types

from config import *
from services.service import check_word, send_message_ia
from handlers import handler_admin

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    style='{',
                    format='#{levelname:8} | {filename} | {name} | {lineno} : "{message}"')

config: Config = load_config()

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
client = TelegramClient('kord', config.client.api_id, config.client.api_hash, loop=loop)
client.start()

bot = Bot(token=config.tg_bot.token,
          default=DefaultBotProperties(parse_mode='MARKDOWN'))
dp = Dispatcher()
dp.include_router(handler_admin.router)
loop.create_task(dp.start_polling(bot))


@dp.message(filters.Command(commands=['parsing_channel']))
async def old_news(message: types.Message):
    days: int = 1
    arr_text = message.text.split(" ")
    if len(arr_text) > 1:
        if arr_text[1].isdigit():
            days = int(arr_text[1])
    offset_date = datetime.today().date() - timedelta(days=days)
    for id1 in channels_id:
        iter_messages = client.iter_messages(entity=id1, offset_date=offset_date, reverse=True)
        async for message in iter_messages:
            if message.date.date() != datetime.today().date():
                word: str = check_word(message.text, key_words2)
                if word:
                    await send_message_ia(bot, message, word)


@client.on(events.NewMessage(chats=channels_id, func=lambda e: e.message.message))
async def handler(event):
    word: str = check_word(event.message.text, key_words)
    if word:
        await send_message_ia(bot, event.message, word)


date = datetime.now().time().strftime('%H:%M')
logger.info(f'Start bot at {date}')

client.run_until_disconnected()
