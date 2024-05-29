from telethon import TelegramClient, events
import config
import asyncio

from datetime import datetime

from handlers.handler1 import send_in_console, parsing_old_message
from aiogram import Bot, Dispatcher

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
client = TelegramClient('kord', config.api_id, config.api_hash)
client.start()


bot = Bot(token=config.bot_token)
dp = Dispatcher()


if __name__ == '__main__':
    print(datetime.now().time().strftime('%H:%M'))
    print('Parsing yesterday news:')
    loop.create_task(dp.start_polling(bot))
    loop.create_task(parsing_old_message(client, bot))
    client.run_until_disconnected()

