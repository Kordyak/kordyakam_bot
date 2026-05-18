import io
import os

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.filters.command import CommandObject
from aiogram.types import Message, FSInputFile

from Services.Converters import *
from Services.Reader import Reader

router_converter = Router(name='converter')


@router_converter.message(Command('trans'))
async def handler(message: Message, command: CommandObject):

    if message.reply_to_message:
        eng_text = await translator(message.reply_to_message.text)
    elif message.quote:
        eng_text = await translator(message.quote.text)
    else:
        eng_text = await translator(command.args)

    if eng_text:
        await message.reply(f'{eng_text}')
    else:
        await message.answer('Текст не обнаружен, вставьте его после команды!')


@router_converter.message(Command('convert'))
async def handler(message: Message, command: CommandObject):
    msg = await message.answer('Подготавливаю аудио...')
    text = command.args
    if message.reply_to_message:  # Если ответить
        if message.reply_to_message.text:  # Если ответить на текст
            text = message.reply_to_message.text

        elif message.reply_to_message.caption:  # Если ответить на картинку с подписью
            text = message.reply_to_message.caption

    if text:
        name_file = make_title(text)
        await convert_text_audio(text, name_file + ".mp3", 90, "")
        audio = FSInputFile(name_file + ".mp3")
        await message.reply_audio(
            audio=audio,
            performer=message.bot._me.first_name,
            title=name_file,
        )
        os.remove(audio.filename)

    else:
        await message.answer('Текст не обнаружен, вставьте его после команды!')

    await msg.delete()

# титул из текста
def make_title(text, words=6, max_len=60):
    clean = re.sub(r'[<>:"/\\|?*]', '', text)
    title = " ".join(clean.split()[:words])
    return title[:max_len]


