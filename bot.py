from telethon import TelegramClient
import config
import asyncio
from telethon import events

from datetime import datetime

from handlers.handler1 import send_message_IA



loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
client = TelegramClient('kord', config.api_id, config.api_hash, loop=loop)
client.start()

@client.on(events.NewMessage(chats=config.channel_url))  # Слушает каналы на сообщение
async def handler(event):
    print(event.message.date)
    print(event.message.sender.username)
    print(event.message.text[:100])
    print('=' * 100)
    await send_message_IA(event.message)

# loop.create_task(parsing_old_message(client))


if __name__ == '__main__':
    print(datetime.now().time())
    client.run_until_disconnected()
