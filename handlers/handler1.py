import re
from datetime import datetime, timedelta
from pprint import pprint

from aiogram import Bot, types, enums, Dispatcher, F
from telethon import TelegramClient
import config


bot = Bot(token=config.BOT_TOKEN)

async def send_message(message: types.Message):  # Отправляет сообщение через бота
    link = f"https://t.me/{message.sender.username}/{message.id}"
    text = f'{link}\n{message.text}'
    print('')
    print(message.date)
    print(f'{link}\n{message.text[:100]}')
    print('=' * 100)
    if check_word(message.text):
        print('Word checked!')
        await bot.send_message(chat_id=config.group_IA_id,  # Чат ИА id
                               text=text,
                               parse_mode=enums.ParseMode.MARKDOWN)


# async def parsing_old_message(client: TelegramClient, bot: Bot):  # парсинг вчерашних новостей
#     offset_date = datetime.today().date() - timedelta(days=1)
#
#     for channel_id in config.channel_id:
#         iter_messages = client.iter_messages(entity=channel_id, offset_date=offset_date, reverse=True)
#
#         async for message in iter_messages:
#             if message.date.date() == offset_date:
#                 await send_message(message.text, bot)
#     client.disconnect()

# @dp.message(F.in_(config.key_words))
# async def send_echo(message: types.Message):
#     await message.reply(text=message.text)


def check_word(news: str):  # парсинг новостей на слово
    for pattern in config.key_words:
        if re.search(pattern, news.lower()):
            return True