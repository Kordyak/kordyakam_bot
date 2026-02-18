
import os

from aiogram import Router, F
from aiogram.types import Message
from aiogram.filters import Command

start_router = Router(name='start')

# start RDP
@start_router.message(F.text.regexp(r"^\d{6}$"))
async def run_rdp(message: Message):
    os.system(f"start call_process_by_time.exe {message.text}")


# start RDP
@start_router.message(Command('start'))
async def run_rdp(message: Message):
    text = (
        f"Привет друг, меня зовут @KordyakBot.\n\n"
        "Мой создатель Андрей Кордяк.\n"
        "- Я умею читать книги в формате Epub на английском по заданному времени для тех изучает английский язык.\n"
        "- Переводить рус-англ и обратно.\n"
        "- Конвертирую текст в аудио на рус. и англ.\n"
        "- Конвертирую аудиособщения в текст на рус.\n"
        ""
    )
    await message.answer(text,)