import asyncio
import logging

from telethon import TelegramClient, events
from config import *

from datetime import datetime

from handlers.handler1 import send_message_IA, check_word, parsing_old_message

from aiogram import Bot, Dispatcher, F, types, filters, enums
from aiogram.client.default import DefaultBotProperties

import environs

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    style='{',
                    format='#{levelname:8} | {filename} | {name} | {lineno} : "{message}"')

env = environs.Env()
env.read_env('.env')
API_ID = env.int('API_ID')
API_HASH: str = env.str('API_HASH')
BOT_TOKEN: str = env.str('BOT_TOKEN')

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

client = TelegramClient('kord2', API_ID, API_HASH, loop=loop)
client.start()

bot = Bot(token=BOT_TOKEN,
          default=DefaultBotProperties(parse_mode=enums.ParseMode.MARKDOWN))
dp = Dispatcher()


@dp.message(filters.Command(commands=['parsing_channel']))
async def old_news(message: types.Message):
    logger.info(message.text)

    days: int = 1
    arr_text = message.text.split(" ")
    if len(arr_text) > 1:
        if arr_text[1].isdigit():
            days = int(arr_text[1])

    await parsing_old_message(client, bot, days)


#Слушает новости и кидает в чат по ключевым словам
@client.on(events.NewMessage(chats=channels_id, func=lambda e: e.message.message))
async def handler(event):
    message = event.message
    link = f"https://t.me/{message.sender.username}/{message.id}"
    text = f'{link}\n{message.text}'
    print('')
    print(message.date)
    print(f'{link}\n{message.text[:150]}')
    print('*' * 50)
    if check_word(message.text, key_words) and not check_word(message.text, key_words_not):
        await send_message_IA(message, bot)


if __name__ == '__main__':
    try:
        date = datetime.now().time().strftime('%H:%M')
        logger.info(f'Started listening to the news at {date}')
        loop.create_task(dp.start_polling(bot))
        client.run_until_disconnected()
    except Exception as e:
        print(e)
        input('Пауза чтоб не закрылась прога!')
        client.disconnect()
        loop.close()
