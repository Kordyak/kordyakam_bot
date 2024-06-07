import telethon.events.common
from telethon import TelegramClient, events
from config import *
import asyncio

from datetime import datetime

from handlers.handler1 import send_message_IA, check_word, parsing_old_message
from aiogram import Bot, Dispatcher, F, types, filters

import environs

env = environs.Env()
env.read_env('.env')
API_ID = env.int('API_ID')
API_HASH: str = env.str('API_HASH')
BOT_TOKEN: str = env.str('BOT_TOKEN')

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
client = TelegramClient('kord2', API_ID, API_HASH, loop=loop)
client.start()

bot = Bot(BOT_TOKEN)
dp = Dispatcher()


@dp.message(filters.Command(commands=['parsing_channel']))
async def old_news(message: types.Message):
    print(message.text)
    await parsing_old_message(client, bot, 1)


#Слушает новости и кидает в чат по ключевым словам
@client.on(events.NewMessage(chats=channel_id, func=lambda e: e.message.message))
async def handler(event):
    message = event.message
    link = f"https://t.me/{message.sender.username}/{message.id}"
    text = f'{link}\n{message.text}'
    print('')
    print(message.date)
    print(f'{link}\n{message.text[:150]}')
    print('*' * 50)
    if check_word(message.text, key_words) and not check_word(message.text, key_words_not):
        await send_message_IA(message)


if __name__ == '__main__':
    try:
        date = datetime.now().time().strftime('%H:%M')
        print(f'Started listening to the news at {date}:')
        loop.create_task(dp.start_polling(bot))
        client.run_until_disconnected()
    except Exception as e:
        print(e)
        input('Пауза чтоб не закрылась прога!')
        client.disconnect()
        loop.close()
