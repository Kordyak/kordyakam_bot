from config import group_ia_id
from aiogram import Bot, types
import re
from datetime import datetime, timedelta
from telethon import TelegramClient
from config import key_words2, channels_id


async def send_message_ia(bot: Bot, message, word: str = ""):
    link = f"https://t.me/{message.sender.username}/{message.id}"
    text = f'key: "{word}"\n{message.text}\n{link}'
    await bot.send_message(chat_id=group_ia_id,  # Чат ИА id
                           text=text)


def check_word(news: str, words: list) -> str:  # парсинг новостей на слово
    for word in words:
        if re.search(word, news.lower()):
            return word


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
                word: str = check_word(message.text, key_words2)
                if word:
                    await send_message_ia(bot, message, word)

