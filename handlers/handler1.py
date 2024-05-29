import re
from datetime import datetime, timedelta
from pprint import pprint

from aiogram import Bot, types, enums, Dispatcher
from telethon import TelegramClient
import config



async def send_in_console(message: types.Message, bot: Bot):  # Отправляет сообщение через бота
    link = f"https://t.me/{message.sender.username}/{message.id}"
    print(message.date)
    print(f'{link}\n{message.text[:100]}')
    print('=' * 100)



async def parsing_old_message(client: TelegramClient, bot: Bot):  # парсинг вчерашних новостей
    offset_date = datetime.today().date() - timedelta(days=1)

    for channel_id in config.channel_id:
        iter_messages = client.iter_messages(entity=channel_id, offset_date=offset_date, reverse=True)

        async for message in iter_messages:
            if message.date.date() == offset_date:
                if check_word(str(message.text)):
                    link = f"https://t.me/{message.sender.username}/{message.id}"
                    text = f'{link}\n{message.text}'
                    if check_word(message.text):
                        await bot.send_message(chat_id=config.group_IA_id,  # Чат ИА id
                                               text=text,
                                               parse_mode=enums.ParseMode.MARKDOWN)
    client.disconnect()


def check_word(news: str):  # парсинг новостей на слово
    for pattern in config.key_words:
        if re.search(pattern, news.lower()):
            return True