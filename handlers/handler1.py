import re
from datetime import datetime, timedelta
from aiogram import Bot, Router
from config import *
from telethon import TelegramClient

router = Router()


async def send_message_IA(message, bot: Bot, word: str = ""):  # Отправляет сообщение через бота
    print('Send message to chat!')
    print(message.date)
    link = f"https://t.me/{message.sender.username}/{message.id}"
    text = f'key:"{word}"\n{message.text}\n{link}'
    await bot.send_message(chat_id=group_IA_id,  # Чат ИА id
                           text=text)


async def Parsing_old_message(client: TelegramClient, bot: Bot, days: int):  # парсинг вчерашних новостей
    offset_date = datetime.today().date() - timedelta(days=days)
    for id1 in channels_id:
        iter_messages = client.iter_messages(entity=id1, offset_date=offset_date, reverse=True)
        async for message in iter_messages:
            if message.date.date() != datetime.today().date():
                word: str = Check_word(message.text, key_words2)
                if word:
                    await send_message_IA(message, bot, word)


def Check_word(news: str, words: list) -> str:  # парсинг новостей на слово
    for word in words:
        if isinstance(news, str):
            if re.search(word, news.lower()):
                return word
