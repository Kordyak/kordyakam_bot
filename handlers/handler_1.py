from aiogram import Router, types, filters, Bot
from aiogram.filters import Command
from aiogram.filters.command import CommandObject
from aiogram.types import Message, BotCommand, FSInputFile


from services.service_1 import *

router = Router(name='Kordyak_router')


@router.message(lambda m: m.text.isdigit() and len(m.text) == 6)
async def run_rdp(message: types.Message):
    #os.system(f"Run_rdp.exe {message.text}")
    os.system(f"start call_process_by_time.exe {message.text}")


@router.message(Command('ru_en', 'en_ru'))
async def handler(message: Message):
    how_translate = message.text.split(' ')[0]
    if message.reply_to_message:
        eng_text = translate_rus_eng(message.reply_to_message.text, how_translate)
    elif message.quote:
        eng_text = translate_rus_eng(message.quote.text, how_translate)
    else:
        eng_text = translate_rus_eng(message.text, how_translate)

    if eng_text:
        await message.reply(f'{eng_text}')


@router.message(Command('audio_eng', 'audio_ru'))
async def handler(message: Message, command: CommandObject):
    text = command.args
    if message.reply_to_message: # Если просто текст в АУДИО перевести когда репли делаешь
        if message.reply_to_message.text: # Если просто текст в АУДИО перевести когда репли делаешь
            text = message.reply_to_message.text

        elif message.reply_to_message.caption: # Текст из чата про книги в АУДИО (капча под картинкой)
            match = re.search(r'Description:\s*(.*?)\s*Read book', message.reply_to_message.caption, re.DOTALL)
            if match:
                text = match.group(1).strip()
            else:
                text = message.reply_to_message.caption

    # else: # когда просто отправляешь текст с командой /audio_eng
    #     text = message.text.replace('/*','')
    #     text = text.replace('@KordyakBot','')

    #text = re.sub(r'[^\w\s.,!?;:()\-–—\"\']', '', text) #Удаляет эмодзи и специальные символы

    if check_english_content(text):  #Проверяет, является ли текст преимущественно английским
        lang = "en"
    elif command.command == "audio_ru":
        lang = "ru"
    else:
        await message.reply("Текст преимущественно (70%) не на английском!!!")

    audio_file: FSInputFile = convert_text_audio(text,"",lang)
    await message.reply_audio(audio_file,
                              performer=message.bot._me.first_name,
                              title=audio_file.filename,
                              )
    os.remove(audio_file.filename)

#@router.message()
#async def handler(message: Message):
#    await message.reply(f"<tg-spoiler>{message.text}</tg-spoiler>", parse_mode="html")




