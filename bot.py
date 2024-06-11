import asyncio
import logging

from telethon import TelegramClient, events
from config import *

from datetime import datetime

from handlers.handler1 import send_message_IA, Check_word, Parsing_old_message

from aiogram import Bot, Dispatcher, F, types, filters, enums
from aiogram.client.default import DefaultBotProperties

from config import Config, Load_config

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    style='{',
                    format='#{levelname:8} | {filename} | {name} | {lineno} : "{message}"')

config: Config = Load_config()


def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    client = TelegramClient('kord', config.client.api_id, config.client.api_hash, loop=loop)
    client.start()

    bot = Bot(token=config.tg_bot.token,
              default=DefaultBotProperties(parse_mode='MARKDOWN'))
    dp = Dispatcher()

    @dp.message(filters.Command(commands=['parsing_channel']))
    async def old_news(message: types.Message):
        days: int = 1
        arr_text = message.text.split(" ")
        if len(arr_text) > 1:
            if arr_text[1].isdigit():
                days = int(arr_text[1])
        await Parsing_old_message(client, bot, days)

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
        word: str = Check_word(message.text, key_words)
        if word:
            await send_message_IA(message, bot, word)

    loop.create_task(dp.start_polling(bot))
    client.run_until_disconnected()


if __name__ == '__main__':
    while True:
        try:
            date = datetime.now().time().strftime('%H:%M')
            logger.info(f'Started listening to the news at {date}')
            asyncio.run(main())

        except Exception as e:
            logger.exception(e)
