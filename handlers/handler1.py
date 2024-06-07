import asyncio
import re
from datetime import datetime, timedelta
from pprint import pprint

from aiogram import Bot, types, enums, Dispatcher, F
from telethon import TelegramClient
from config import *

from telethon import TelegramClient, events

bot = Bot(token=BOT_TOKEN)


async def send_message_IA(message):  # Отправляет сообщение через бота
    print('Send message to chat!')
    link = f"https://t.me/{message.sender.username}/{message.id}"
    text = f'{link}\n{message.text}'
    await bot.send_message(chat_id=group_IA_id,  # Чат ИА id
                           text=text,
                           parse_mode=enums.ParseMode.MARKDOWN)


async def parsing_old_message(client: TelegramClient, key_words: list, days: int):  # парсинг вчерашних новостей
    offset_date = datetime.today().date() - timedelta(days=days)

    for id in channel_id:
        iter_messages = client.iter_messages(entity=id, offset_date=offset_date, reverse=True)

        async for message in iter_messages:
            if message.date.date() != datetime.today().date():
                if check_word(message.text, key_words2):
                    if not check_word(message.text, key_words_not):
                        await send_message_IA(message)

    client.disconnect()


def check_word(news: str, key_words: list):  # парсинг новостей на слово
    for pattern in key_words:
        if isinstance(news, str):
            if re.search(pattern, news.lower()):
                return True
