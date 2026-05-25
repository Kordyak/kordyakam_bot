import io
import os

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.filters.command import CommandObject
from aiogram.types import Message, FSInputFile

from Services.Converters import *
from Services.Reader import Reader

router_converter = Router(name='converter')


def extract_text(message: Message, command: CommandObject) -> str | None:
    if message.reply_to_message:
        return message.reply_to_message.text or message.reply_to_message.caption
    if message.quote:
        return message.quote.text
    return command.args


@router_converter.message(Command('trans'))
async def handler_trans(message: Message, command: CommandObject):
    msg = await message.answer('⏳')
    text = extract_text(message, command)
    eng_text = await translator(text) if text else None

    if eng_text:
        await message.reply(eng_text)
    else:
        await message.answer('Текст не обнаружен, вставьте его после команды!')

    await msg.delete()


@router_converter.message(Command('convert'))
async def handler_convert(message: Message, command: CommandObject):
    msg = await message.answer('⏳')
    text = extract_text(message, command)

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


