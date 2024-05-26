from datetime import datetime, timedelta

import config
from aiogram import Bot
from aiogram.enums import ParseMode
import asyncio
from telethon import events

bot = Bot(token=config.bot_token)
date_check = datetime.today().date()

async def client_overhear(client):
    channel_source = [
        'https://t.me/channelOut2',
        'https://t.me/meduzalive',
        'https://t.me/LipsitsIgor',
        'https://t.me/bdtprb',
    ]
    @client.on(events.NewMessage(chats=channel_source))  # Слушает каналы на сообщение
    async def handler(event):
        await send_message_IA(event.message)  # Отправляет сообщение через бота в группу ИА
        await parsing_old_message(client)


async def send_message_IA(message):  # Отправляет сообщение через бота
    arr_words = [
        "главные новости",
        "национализация",
        "мобилизация",
        "путин",
        "бпла",
    ]
    print('send_message_IA 1')
    for i in range(len(arr_words)):
        if arr_words[i] in message.text.lower():
            link = f"https://t.me/{message.sender.username}/{message.id}"
            print('send_message_IA 2')
            print(link)
            await bot.send_message(chat_id=config.group_IA_id,  # Чат ИА id
                                   text=f'{link}\n{message.text}',
                                   parse_mode=ParseMode.MARKDOWN)
            break


async def parsing_old_message(client):  # Парсер старых сообщений в МЕДУЗЕ, последние 20 сообщений
    # while True:
        print('parsing_old_message 1')
        global date_check
        offset_date = datetime.today().date() + timedelta(days=1)
        iter_messages = client.iter_messages(config.channel_meduza_id, offset_date=offset_date)  # все сообщения до даты
        i = 0
        if offset_date != date_check:
            print('parsing_old_message 2')
            async for message in iter_messages:
                if 'Главные новости' in message.text:
                    print('parsing_old_message 3')
                    date_check = offset_date
                    await send_message_IA(message)
                    break
                elif i == 20:  # проверяем 20 сообщений
                    break
                else:
                    i += 1
        # await asyncio.sleep(3600)


