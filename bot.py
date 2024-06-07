import telethon.events.common
from telethon import TelegramClient, events
from config import *
import asyncio

from datetime import datetime

from handlers.handler1 import send_message_IA, check_word
from aiogram import Bot, Dispatcher, F, types

import environs

env = environs.Env
env.read_env()
API_ID: int = env.int('API_ID')
API_HASH: str = env.str('API_HASH')

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
client = TelegramClient('kord2', API_ID, API_HASH, loop=loop)
client.start()

# Слушает новости и кидает в чат по ключевым словам

@client.on(events.NewMessage(chats=channel_id, func=lambda e: e.message.message))  # Слушает каналы
async def handler(event):
    message = event.message
    link = f"https://t.me/{message.sender.username}/{message.id}"
    text = f'{link}\n{message.text}'
    print('')
    print(message.date)
    print(f'{link}\n{message.text[:150]}')
    print('*' * 50)
    if check_word(message.text, key_words) and not check_word(message.text, key_words_not) :
        await send_message_IA(message)


if __name__ == '__main__':
    date = datetime.now().time().strftime('%H:%M')
    print(f'Started listening to the news at {date}:')
    try:
        client.run_until_disconnected()
    except Exception as e:
        print(e)
        input('Пауза чтоб не закрылась прога')
        client.disconnect()
        loop.close()

