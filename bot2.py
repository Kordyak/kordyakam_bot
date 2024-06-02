from telethon import TelegramClient, events
import config
import asyncio

from datetime import datetime

from handlers.handler1 import send_message_IA, parsing_old_message
from aiogram import Bot, Dispatcher

# Парсинг старых новостей вчерашних дней по ключевым фразам

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
client = TelegramClient('kord2', config.api_id, config.api_hash)
client.start()


if __name__ == '__main__':
    print(datetime.now().time().strftime('%H:%M'))
    print('Parsing yesterday news:')
    days_ago = input('Сколько дней назад пропарсить ТГ каналы: ') or '1'
    loop.create_task(
        parsing_old_message(
            client,
            config.key_words2,
            int(days_ago)
        ))
    client.run_until_disconnected()

