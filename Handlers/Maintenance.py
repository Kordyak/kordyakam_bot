import os
from pathlib import Path

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.filters import Command

from Keyboards.Universal import confirm_kb
from SQL.RR_sql import ReadRepository

start_router = Router(name='start')


# start call_process_by_time
@start_router.message(F.text.regexp(r"^\d{6}$"))
async def run_rdp(message: Message, user_id: int):
    if user_id == 995657021:
        os.system(f"start call_process_by_time.exe {message.text}")
        await message.delete()


@start_router.message(Command("hibernate"))
async def stop_bot(message: Message, user_id: int):
    if user_id == 995657021:
        await message.answer('Вы уверены?', reply_markup=confirm_kb('hibernate'))


@start_router.message(Command("reboot"))
async def stop_bot(message: Message, user_id: int):
    if user_id == 995657021:
        await message.answer('Вы уверены?', reply_markup=confirm_kb('reboot'))


@start_router.message(Command("exit"))
async def stop_bot(message: Message, user_id: int):
    if user_id == 995657021:
        await message.answer('Вы уверены?', reply_markup=confirm_kb('exit'))


@start_router.message(Command("sql"))
async def migration(message: Message, user_id: int):
    if user_id == 995657021:
        await message.answer('Сервисный режим SQL')
        # rr = ReadRepository(Path("SQL/read.db"))
        # repo.migrate_books_index(Path("Books/books_index.json"))
        # repo.migrate_states(Path("Users"))
        # user = rr.get_user_state(user_id)
        # print("")
