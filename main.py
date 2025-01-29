import asyncio
import logging
import re
import os

from telethon import events, TelegramClient

from datetime import datetime, timedelta

from aiogram import Dispatcher, Bot, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import Message, BotCommand, FSInputFile

from config import *
from services.service import check_word, translate_rus_eng, convert_text_audio
from handlers import handler_admin

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    style='{',
                    format='#[{asctime}] #{levelname} | {name} | : "{message}"')
logger.info(f'Start bot!!!')

config: Config = load_config()

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

client = TelegramClient('kord2', config.client.api_id, config.client.api_hash)
client.start()

bot = Bot(token=config.tg_bot.token,
          default=DefaultBotProperties(parse_mode='MARKDOWN'))
commands = [
    #BotCommand(command="/start", description="Запустить бота"),
    BotCommand(command="/eng", description="Перевести рус. - англ."),
    BotCommand(command="/audio", description="Конвертировать текст в аудио на англ."),
]


dp = Dispatcher()
dp.include_router(handler_admin.router)

loop.create_task(dp.start_polling(bot))
dp['client'] = client


async def set_bot_commands():
    await bot.set_my_commands(commands)

loop.create_task(set_bot_commands())


@client.on(events.NewMessage(chats=channels_id))
async def handler(event: events):
    key: str = check_word(event.message.text, key_words)
    if key:
        message_link = f"https://t.me/{event.message.chat.username}/{event.message.id}"
        eng_text = translate_rus_eng(event.message.text)
        await bot.send_message(chat_id=chat_id_IA, text=f'{eng_text}\n{message_link}')

@dp.message(F.text, Command('eng'))
async def handler(message: Message):
    eng_text: str
    message_link: str
    if message.reply_to_message:
        message_link = f"https://t.me/{message.chat.username}/{message.message_id}"
        eng_text = translate_rus_eng(message.reply_to_message.text)
    elif message.quote:
        message_link = f"https://t.me/{message.external_reply.chat.username}/{message.external_reply.message_id}"
        eng_text = translate_rus_eng(message.quote.text)

    if eng_text:
        await message.reply(f'{eng_text}\n{message_link}')


@dp.message(F.text, Command('audio'))
async def handler(message: Message):
    audio_file: FSInputFile = convert_text_audio(message.reply_to_message.text)
    await message.reply_audio(audio_file)
    os.remove(audio_file.filename)





client.run_until_disconnected()






# if __name__ == '__main__':
#     client.run_until_disconnected()

# async def my_channels():
#     dialogs = await client.get_dialogs()
#     for dialog in dialogs:
#         if dialog.is_channel:
#                 channels_id.append(dialog.id)
#             channels_id.append(f"https://t.me/{dialog.entity.username}")
#             print(f"{dialog.id} | {dialog.entity.username} | {dialog.id}")
#
# loop.create_task(my_channels())