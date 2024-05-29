from telethon import TelegramClient, events
import config
import asyncio

from datetime import datetime

from handlers.handler1 import send_message_IA, parsing_old_message
from aiogram import Bot, Dispatcher


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


bot = Bot(token=config.bot_token)
dp = Dispatcher()
@dp.message()
async def send_echo(message):
    await message.reply(text=message.text)
    await asyncio.sleep(5)




if __name__ == '__main__':
    print(datetime.now().time())
    print('Hearing news!')

    loop.create_task(parsing_old_message(client, bot))
    loop.create_task(dp.start_polling(bot))

    # loop2 = asyncio.get_event_loop()

    client.run_until_disconnected()

