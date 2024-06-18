import asyncio
import logging

from telethon import events, TelegramClient

from datetime import datetime, timedelta

from aiogram import Dispatcher, Bot
from aiogram.client.default import DefaultBotProperties
from aiogram import filters, types

from config import *
from services.service import check_word, send_message_ia, old_news
from handlers import handler_admin

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    style='{',
                    format='#[{asctime}] #{levelname} | {name} | : "{message}"')

config: Config = load_config()

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
client = TelegramClient('kord2', config.client.api_id, config.client.api_hash)
client.start()

bot = Bot(token=config.tg_bot.token,
          default=DefaultBotProperties(parse_mode='MARKDOWN'))
dp = Dispatcher()
dp.include_router(handler_admin.router)



@client.on(events.NewMessage(chats=channels_id))
async def handler(event):
    await send_message_ia(bot, event.message)
    # word: str = check_word(event.message.text, key_words)
    # if word:
    #     await send_message_ia(bot, event.message, word)


@dp.message(filters.Command(commands=['parsing_channel']))
async def old_news_handler(message: types.Message):
    await old_news(message, bot, client)


date = datetime.now().time().strftime('%H:%M')
logger.info(f'Start bot at {date}')

loop.create_task(dp.start_polling(bot))
client.run_until_disconnected()
