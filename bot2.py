from telethon import TelegramClient, events
from config import *
import asyncio

from datetime import datetime

from handlers.handler1 import send_message_IA, parsing_old_message
from aiogram import Bot, Dispatcher

# Парсинг старых новостей вчерашних дней по ключевым фразам

import environs

env = environs.Env
env.read_env()
API_ID: int = env.int('API_ID')
API_HASH: str = env.str('API_HASH')

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
client = TelegramClient('kord2', API_ID, API_HASH)
client.start()


if __name__ == '__main__':
    print(datetime.now().time().strftime('%H:%M'))
    print('Parsing yesterday news:')
    days_ago = input('Сколько дней назад пропарсить ТГ каналы (по умолчанию 1 день): ') or '1'
    loop.create_task(
        parsing_old_message(
            client,
            key_words2,
            int(days_ago)
        ))
    client.run_until_disconnected()

