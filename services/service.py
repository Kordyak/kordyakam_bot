from config import group_ia_id
from aiogram import Bot
import re


async def send_message_ia(bot: Bot, message, word: str = ""):
    link = f"https://t.me/{message.sender.username}/{message.id}"
    text = f'key: "{word}"\n{message.text}\n{link}'
    await bot.send_message(chat_id=group_ia_id,  # Чат ИА id
                           text=text)


def check_word(news: str, words: list) -> str:  # парсинг новостей на слово
    for word in words:
        if isinstance(news, str):
            if re.search(word, news.lower()):
                return word
