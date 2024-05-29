from telethon import TelegramClient, events
import config
import asyncio

from datetime import datetime

from handlers.handler1 import send_message
from aiogram import Bot, Dispatcher, F, types

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
client = TelegramClient('kord', config.api_id, config.api_hash, loop=loop)
client.start()


@client.on(events.NewMessage(chats=config.channel_url))  # Слушает каналы
async def handler(event):
    await send_message(event.message, config.key_words)


if __name__ == '__main__':
    print(datetime.now().time().strftime('%H:%M'))
    print('Starts listening news:')
    client.run_until_disconnected()
