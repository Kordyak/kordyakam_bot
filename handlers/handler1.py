import re
from datetime import datetime, timedelta
from pprint import pprint

from aiogram import Bot, types
from aiogram.enums import ParseMode

import config

bot = Bot(token=config.bot_token)
date_check = datetime.today().date()


async def send_message_IA(message: types.Message):  # Отправляет сообщение через бота
    if check_word(message.text):
        print('send_message_IA'*5)
        print('\n')
        link = f"https://t.me/{message.sender.username}/{message.id}"
        await bot.send_message(chat_id=config.group_IA_id,  # Чат ИА id
                               text=f'{link}\n{message.text}',
                               parse_mode=ParseMode.MARKDOWN)


def check_word(news: str):  # парсинг нововстей на слово
    for pattern in config.arr_patterns:
        if re.search(pattern, news.lower()):
            return True


async def parsing_old_message(client):  # Парсер вчерашних сообщений
    offset_date = datetime.today().date() - timedelta(days=1)

    for channel_id in config.channel_id:
        iter_messages = client.iter_messages(entity=channel_id, offset_date=offset_date, reverse=True)

        async for message in iter_messages:
            if message.date.date() == offset_date:
                if check_word(str(message.text)):
                    await send_message_IA(message)

