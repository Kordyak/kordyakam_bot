from aiogram import Router, types, filters, Bot
import os

from aiogram import Dispatcher, Bot, F
from aiogram.client.default import DefaultBotProperties
from aiogram.filters import Command
from aiogram.types import Message, BotCommand, FSInputFile

import re

from services.service_1 import check_word, translate_rus_eng, convert_text_audio

router = Router()

@router.message(lambda m: m.text.isdigit() and len(m.text) == 6)
async def run_rdp(message: types.Message):
    os.system(f"Run_rdp.exe {message.text}")
    os.system(f"start call_process_by_time.exe")


@router.message(lambda m: re.match(r"^/eng.*", m.text)  )
async def handler(message: Message):
    eng_text: str
    message_link: str
    text = message.text.replace("/eng","")
    if message.reply_to_message:
        message_link = f"https://t.me/{message.chat.username}/{message.message_id}"
        eng_text = translate_rus_eng(message.reply_to_message.text)
    elif message.quote:
        message_link = f"https://t.me/{message.external_reply.chat.username}/{message.external_reply.message_id}"
        eng_text = translate_rus_eng(message.quote.text)
    elif len(text.rstrip()) > 3:
        message_link = ""
        eng_text = translate_rus_eng(text)

    if eng_text:
        await message.reply(f'{eng_text}\n{message_link}')


@router.message(Command('audio'))
async def handler(message: Message):
    audio_file: FSInputFile = convert_text_audio(message.reply_to_message.text)
    await message.reply_audio(audio_file)
    os.remove(audio_file.filename)






# @router.message(lambda m: m.text == '/shutdown')
# async def shutdown_pc(message: types.Message):
#     if message.text.split(" ")[1] == 's':
#         os.system(f"shutdown /s")
#     elif message.text.split(" ")[1] == 'h':
#         os.system(f"shutdown /h")
#     elif message.text.split(" ")[1] == 'r':
#         os.system(f"shutdown /r")
