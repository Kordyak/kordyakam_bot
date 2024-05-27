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
        print('send_message_IA')
        print(message.sender.username)
        print('=' * 100)
        link = f"https://t.me/{message.sender.username}/{message.id}"
        await bot.send_message(chat_id=config.group_IA_id,  # Чат ИА id
                               text=f'{link}\n{message.text}',
                               parse_mode=ParseMode.MARKDOWN)

def check_word(news: str): # проверка сообщение на слово
    print('check_word')
    print(news[:50])
    print('\n')
    for i in range(len(config.arr_patterns)):
        pattern = config.arr_patterns[i]
        if re.search(pattern, news):
            print('True')
            return True

async def parsing_old_message(client):  # Парсер старых сообщений
    offset_date = datetime.today().date() + timedelta(days=1)
    i = 0
    async for channel_id in config.channel_id:
        iter_messages = client.iter_messages(channel_id, offset_date=offset_date)  # все сообщения до даты
        async for message in iter_messages:
            if check_word(message.text):
                await send_message_IA(message)
                break
            elif i == 50:
                break
            else:
                i += 1
