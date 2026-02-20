
import os

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.filters import Command

start_router = Router(name='start')

# start RDP call_process_by_time
@start_router.message(F.text.regexp(r"^\d{6}$"))
async def run_rdp(message: Message):
    os.system(f"start call_process_by_time.exe {message.text}")
    await message.delete()


# start RDP
@start_router.message(Command('start'))
async def run_rdp(message: Message, state: FSMContext):
    await state.clear()
    text = (
        f"Привет, друг! Меня зовут <b>{message.bot._me.first_name}</b>.\n\n"
        "Я умею:\n"
        "• Читать книги в формате <b>EPUB</b> на английском по заданному времени — команда /book\n"
        "• Переводить с русского на английский и обратно\n"
        "• Конвертировать текст в аудио (RU / EN)\n"
        "• Конвертировать аудиосообщение в текст (RU)\n"
    )

    await message.answer(text, parse_mode="HTML")
