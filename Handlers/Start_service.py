import os

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.filters import Command

from Keyboards.Universal import confirm_kb

start_router = Router(name='start')


# start RDP call_process_by_time
@start_router.message(F.text.regexp(r"^\d{6}$"))
async def run_rdp(message: Message, user_id: int):
    if user_id == 995657021:
        os.system(f"start call_process_by_time.exe {message.text}")
        await message.delete()


@start_router.message(Command('start'))
async def run_rdp(message: Message, state: FSMContext):
    await state.clear()
    text = (
        f"Привет, друг! Меня зовут <b>{message.bot._me.first_name}</b>.\n\n"
        "Я умею:\n"
        "• Читать книги в формате <b>EPUB</b> на английском по заданному времени — команда /book\n"
        "• Переводить (RU / EN) и обратно\n"
        "• Конвертировать текст в аудио (RU / EN)\n"
        "• Конвертировать аудиосообщения в текст (RU)\n"
    )

    await message.answer(text, parse_mode="HTML")


@start_router.message(Command("exit"))
async def stop_bot(message: Message, user_id: int):
    if user_id == 995657021:
        await message.answer('Вы уверены?', reply_markup=confirm_kb('exit'))


@start_router.message(Command("hibernate"))
async def stop_bot(message: Message, user_id: int):
    if user_id == 995657021:
        await message.answer('Вы уверены?', reply_markup=confirm_kb('hibernate'))
