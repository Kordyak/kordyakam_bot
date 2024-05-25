from telethon import TelegramClient, events

# from config import api_id, api_hash, group_IA_id,channel_meduza_id
import config

from aiogram import Bot
from aiogram.enums import ParseMode

from datetime import datetime, timedelta

import asyncio

bot = Bot(token=config.bot_token)

date_check = datetime.today().date()


async def send_message_IA(message):  # Отправляет сообщение через бота
    arr_words = [
        "главные новости",
        "национализ",
        "мобилизаци",
        "путин",
        "бпла",
    ]

    for i in range(len(arr_words)):
        if arr_words[i] in message.text.lower():
            link = f"https://t.me/{message.sender.username}/{message.id}"
            print(link)
            await bot.send_message(chat_id=config.group_IA_id,  # Чат ИА id
                                   text=f'{link}\n{message.text}',
                                   parse_mode=ParseMode.MARKDOWN)
            break


async def parsing_old_message(client1, offset_date):  # Парсер старых сообщений в МЕДУЗЕ, последние 20 сообщений
    global date_check
    iter_messages = client1.iter_messages(config.channel_meduza_id, offset_date=offset_date)  # все сообщения до даты
    i = 0
    async for message in iter_messages:
        if 'Главные новости' in message.text:
            await send_message_IA(message)
            date_check = offset_date # для проверки чтобы один раз в день парсить МЕДУЗУ
            break
        elif i == 20:  # проверяем 20 сообщений
            break
        else:
            i += 1


async def tg_parser(client1, send_message_func):  # парсер Новых сообщений
    channel_source = [
        'https://t.me/channelOut2',
        'https://t.me/meduzalive',
        'https://t.me/LipsitsIgor',
        'https://t.me/bdtprb',
    ]
    @client1.on(events.NewMessage(chats=channel_source))  # Забирает посты каналов
    async def handler(event):
        print('зашел в хендлер!')
        await send_message_func(event.message)  # Отправляет сообщение через бота

        offset_date = datetime.today().date() + timedelta(days=1)  # день до которого брать сообщения
        if offset_date != date_check:
            await parsing_old_message(client, offset_date)  # Парсер старых сообщений



loop = asyncio.new_event_loop()  # создаем цикл сущность
asyncio.set_event_loop(loop)  # Устанавливаем цикл

session = 'kord'
client = TelegramClient(session, config.api_id, config.api_hash, loop=loop)
client.start()  # Стартуем Клиента

loop.create_task(tg_parser(client, send_message_IA))  # парсер Новых сообщений
client.run_until_disconnected()

# loop.create_task(parsing_old_message(client))  # Парсер старых сообщений




