import telethon.events.common
from telethon import TelegramClient, events
import config
import asyncio

from datetime import datetime

from handlers.handler1 import send_message
from aiogram import Bot, Dispatcher, F, types

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
client = TelegramClient('kord2', config.api_id, config.api_hash, loop=loop)
client.start()

# Слушает новости и кидает в чат по ключевым словам

@client.on(events.NewMessage(chats=config.channel_url))  # Слушает каналы
async def handler(event):
    await send_message(event.message, config.key_words)


if __name__ == '__main__':
    print(datetime.now().time().strftime('%H:%M'))
    print('Starts listening news:')
    try:
        client.run_until_disconnected()
    except Exception as e:
        print(e)
        input('Пауза чтоб не закрылась прога')
        client.disconnect()
        loop.close()

