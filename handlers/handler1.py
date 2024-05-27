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
        if re.match(pattern, news):
            print('True')
            print('='*100)
            pprint(re.match(pattern, news))
            return True



async def parsing_old_message(client):  # Парсер старых сообщений в МЕДУЗЕ, последние 20 сообщений
    # while True:
    print('parsing_old_message 1')
    global date_check
    offset_date = datetime.today().date() + timedelta(days=1)
    iter_messages = client.iter_messages(config.channel_meduza_id, offset_date=offset_date)  # все сообщения до даты
    i = 0
    if offset_date != date_check:
        print('parsing_old_message 2')
        async for message in iter_messages:
            if 'Главные новости' in message.text:
                print('parsing_old_message 3')
                date_check = offset_date
                await send_message_IA(message)
                break
            elif i == 20:  # проверяем 20 сообщений
                break
            else:
                i += 1
    # await asyncio.sleep(3600)
