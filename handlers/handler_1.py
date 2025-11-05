from aiogram import Router, types, filters, Bot
from aiogram.filters import Command
from aiogram.types import Message, BotCommand, FSInputFile

from services.service_1 import *

router = Router()


@router.message(lambda m: m.text.isdigit() and len(m.text) == 6)
async def run_rdp(message: types.Message):
    #os.system(f"Run_rdp.exe {message.text}")
    os.system(f"start call_process_by_time.exe {message.text}")


@router.message(Command('ru_en', 'en_ru'))
async def handler(message: Message):
    how_translate = message.text.split(' ')[0]

    if message.reply_to_message:
        message_link = f"https://t.me/{message.chat.username}/{message.message_id}"
        eng_text = translate_rus_eng(message.reply_to_message.text, how_translate)
    elif message.quote:
        message_link = f"https://t.me/{message.external_reply.chat.username}/{message.external_reply.message_id}"
        eng_text = translate_rus_eng(message.quote.text, how_translate)
    else:
        message_link = ""
        eng_text = translate_rus_eng(message.text, how_translate)

    if eng_text:
        await message.reply(f'{eng_text}')


@router.message(Command('audio'))
async def handler(message: Message):
    if message.reply_to_message.text:
        text = message.reply_to_message.text
    elif message.reply_to_message.caption:
        match = re.search(r'Description:\s*(.*?)\s*Read book', message.reply_to_message.caption, re.DOTALL)
        if match:
            text = match.group(1).strip()
        else:
            text = message.reply_to_message.caption
    else:
        text = message.md_text.replace('/audio','')

    audio_file: FSInputFile = convert_text_audio(text)
    await message.reply_audio(audio_file)
    os.remove(audio_file.filename)



