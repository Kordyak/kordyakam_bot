import asyncio
import re
from datetime import datetime, timedelta
from pprint import pprint

from aiogram import Bot, types, enums, Dispatcher, F
from telethon import TelegramClient
import config

from telethon import TelegramClient, events

bot = Bot(token=config.BOT_TOKEN)


async def send_message_IA(message):  # Отправляет сообщение через бота
    print('Send message to chat!')
    link = f"https://t.me/{message.sender.username}/{message.id}"
    text = f'{link}\n{message.text}'
    await bot.send_message(chat_id=config.group_IA_id,  # Чат ИА id
                           text=text,
                           parse_mode=enums.ParseMode.MARKDOWN)


async def parsing_old_message(client: TelegramClient, key_words: list, days: int):  # парсинг вчерашних новостей
    offset_date = datetime.today().date() - timedelta(days=days)

    for channel_id in config.channel_id:
        iter_messages = client.iter_messages(entity=channel_id, offset_date=offset_date, reverse=True)

        async for message in iter_messages:
            if message.date.date() != datetime.today().date():
                if (check_word(message.text, config.key_words2) and
                        not check_word(message.text, config.key_words_not)):
                    await send_message_IA(message)

    client.disconnect()


def check_word(news: str, key_words: list):  # парсинг новостей на слово
    for pattern in key_words:
        if isinstance(news, str):
            return re.search(pattern, news.lower())
