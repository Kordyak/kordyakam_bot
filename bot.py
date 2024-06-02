import telethon.events.common
from telethon import TelegramClient, events
import config
import asyncio

from datetime import datetime

from handlers.handler1 import send_message_IA, check_word
from aiogram import Bot, Dispatcher, F, types

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
client = TelegramClient('kord2', config.api_id, config.api_hash, loop=loop)
client.start()

# Слушает новости и кидает в чат по ключевым словам

@client.on(events.NewMessage(chats=config.channel_id, func=lambda e: e.message.message))  # Слушает каналы
async def handler(event):
    message = event.message
    link = f"https://t.me/{message.sender.username}/{message.id}"
    text = f'{link}\n{message.text}'
    print('')
    print(message.date)
    print(f'{link}\n{message.text[:150]}')
    print('*' * 50)
    if check_word(message.text, config.key_words):
        await send_message_IA(message)


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

