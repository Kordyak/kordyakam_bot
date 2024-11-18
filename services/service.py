from config import group_ia_id
from aiogram import Bot, types
import re
from datetime import datetime, timedelta
from telethon import TelegramClient
from config import key_words2, channels_id, key_words_not

import logging

from googletrans import Translator
import re

logger = logging.getLogger(__name__)


async def send_message_ia(bot: Bot, message, key: str = ""):
    link = f"https://t.me/{message.sender.username}/{message.id}"
    clean_text = message.text.replace('*', '')
    result_re = re.sub('\(.*?\)', "", clean_text)
    translator = Translator()
    result_translate = translator.translate(text=result_re, src='ru', dest='en')
    text = f'key: "{key}"\n{result_translate.text}\n{link}'
    await bot.send_message(chat_id=group_ia_id, text=text)


async def send_message_user(bot: Bot, message, chat_id: int, key: str = ""):
    link = f"https://t.me/{message.sender.username}/{message.id}"
    text = f'key: "{key}"\n{message.text}\n{link}'
    await bot.send_message(chat_id=chat_id,  # 1286023315 Чат Иринки / 995657021 мой чат
                           text=text)


def check_word(news: str, words: list) -> str:  # парсинг новостей на слово
    for key in words:
        if re.search(key, news.lower()):
            return key


async def old_news(message: types.Message, bot: Bot, client: TelegramClient):
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
                key: str = check_word(message.text, key_words2)
                if key:
                    if not check_word(message.text, key_words_not):
                        await send_message_ia(bot, message, key)
                        # print(message.text[:100])
