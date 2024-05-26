from telethon import TelegramClient, events
import config
import asyncio

from handlers.handler1 import send_message_IA, parsing_old_message, client_overhear


def main():
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    client = TelegramClient('kord', config.api_id, config.api_hash, loop=loop)
    client.start()
    loop.create_task(client_overhear(client))
    client.run_until_disconnected()


if __name__ == '__main__':
    main()
