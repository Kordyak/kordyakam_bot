import re
from datetime import datetime, timedelta
from aiogram import Bot, types, enums, Dispatcher, F
from config import *
from telethon import TelegramClient, events


async def send_message_IA(message, bot: Bot):  # Отправляет сообщение через бота
    print('Send message to chat!')
    link = f"https://t.me/{message.sender.username}/{message.id}"
    text = f'{link}\n{message.text}'
    await bot.send_message(chat_id=group_IA_id,  # Чат ИА id
                           text=text,
                           parse_mode=enums.ParseMode.MARKDOWN)


async def parsing_old_message(client: TelegramClient, bot: Bot, days: int):  # парсинг вчерашних новостей
    offset_date = datetime.today().date() - timedelta(days=days)

    for id in channels_id:
        iter_messages = client.iter_messages(entity=id, offset_date=offset_date, reverse=True)

        async for message in iter_messages:
            if message.date.date() != datetime.today().date():
                if check_word(message.text, key_words2):
                    if not check_word(message.text, key_words_not):
                        await send_message_IA(message, bot)
    # client.disconnect()


def check_word(news: str, words: list):  # парсинг новостей на слово
    for word in words:
        if isinstance(news, str):
            if re.search(word, news.lower()):
                return True
