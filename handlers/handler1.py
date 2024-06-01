import asyncio
import re
from datetime import datetime, timedelta
from pprint import pprint

from aiogram import Bot, types, enums, Dispatcher, F
from telethon import TelegramClient
import config

from telethon import TelegramClient, events

bot = Bot(token=config.BOT_TOKEN)


async def send_message(message, key_words: list):  # Отправляет сообщение через бота
    link = f"https://t.me/{message.sender.username}/{message.id}"
    if not message.text:
        print(' не текст!'*3)
        return
    print('')
    print(message.date)
    print(f'{link}\n{message.text[:150]}')
    print('*' * 50)
    text = f'{link}\n{message.text}'
    if check_word(message.text, key_words):
        print('Send message to chat!')
        # await bot.send_message(chat_id=config.group_IA_id,  # Чат ИА id
        #                        text=text,
        #                        parse_mode=enums.ParseMode.MARKDOWN)


async def parsing_old_message(client: TelegramClient, key_words: list, days: int):  # парсинг вчерашних новостей
    offset_date = datetime.today().date() - timedelta(days=days)

    for channel_id in config.channel_id:
        iter_messages = client.iter_messages(entity=channel_id, offset_date=offset_date, reverse=True)

        async for message in iter_messages:
            if message.date.date() != datetime.today().date():
                await send_message(message, key_words)

    client.disconnect()


def check_word(news: str, key_words: list):  # парсинг новостей на слово
    for pattern in key_words:
        if isinstance(news, str):
            if re.search(pattern, news.lower()):
                return True
