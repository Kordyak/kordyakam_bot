import os
from aiogram import Router
from aiogram.filters import Command
from aiogram.filters.command import CommandObject
from aiogram.types import Message, FSInputFile

from Services.Converters import *

router_converter = Router(name='converter')


def extract_text(message: Message, command: CommandObject) -> str | None:
    if message.reply_to_message:
        return message.reply_to_message.text or message.reply_to_message.caption
    if message.quote:
        return message.quote.text
    return command.args


@router_converter.message(Command('trans'))
async def handler_trans(message: Message, command: CommandObject):
    text = extract_text(message, command)

    if text:
        msg = await message.answer('⏳')
        trans_text = await translator(text) if text else None
        await message.reply(trans_text)
        await msg.delete()
    else:
        await message.answer('Текст не обнаружен, вставьте его после команды!')



@router_converter.message(Command('convert'))
async def handler_convert(message: Message, command: CommandObject):
    text = extract_text(message, command)

    if text:
        msg = await message.answer('⏳')
        name_file = make_title(text)
        await convert_text_audio(text, name_file + ".mp3", 90, "")
        audio = FSInputFile(name_file + ".mp3")
        await message.reply_audio(
            audio=audio,
            performer=message.bot._me.first_name,
            title=name_file,
        )
        os.remove(audio.filename)
        await msg.delete()
    else:
        await message.answer('Текст не обнаружен, вставьте его после команды!')




# титул из текста
def make_title(text, words=6, max_len=60):
    clean = re.sub(r'[<>:"/\\|?*]', '', text)
    title = " ".join(clean.split()[:words])
    return title[:max_len]


