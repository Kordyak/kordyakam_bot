from telethon import TelegramClient
import config
import asyncio
from telethon import events

import datetime

from handlers.handler1 import send_message_IA, parsing_old_message


def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    client = TelegramClient('kord', config.api_id, config.api_hash, loop=loop)
    client.start()

    @client.on(events.NewMessage(chats=config.channel_url))  # Слушает каналы на сообщение
    async def handler(event):
        await send_message_IA(event.message)

    # loop.create_task(parsing_old_message(client))
    return client




if __name__ == '__main__':
    print(datetime.datetime.now().time())
    client = main()
    client.run_until_disconnected()
