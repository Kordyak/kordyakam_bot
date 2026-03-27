import os
from pathlib import Path

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.filters import Command
from tokenizers.decoders import Replace

from Keyboards.Universal import confirm_kb
from SQL.RR_sql import ReadRepository

router_maintenance = Router(name='start')


# start call_process_by_time
@router_maintenance.message(F.text.regexp(r"^\d{6}$"))
async def run_rdp(message: Message):
    os.system(f"start call_process_by_time.exe {message.text}")
    await message.delete()


@router_maintenance.message(Command("hibernate"))
async def stop_bot(message: Message):
    await message.answer('Вы уверены?', reply_markup=confirm_kb('hibernate'))


@router_maintenance.message(Command("reboot"))
async def stop_bot(message: Message):
    await message.answer('Вы уверены?', reply_markup=confirm_kb('reboot'))


@router_maintenance.message(Command("exit"))
async def stop_bot(message: Message):
    await message.answer('Вы уверены?', reply_markup=confirm_kb('exit'))


@router_maintenance.message(Command("sql"))
async def migration(message: Message):
    await message.answer('Сервисный режим SQL')
    # rr = ReadRepository(Path("SQL/read.db"))
    # repo.migrate_books_index(Path("Books/books_index.json"))
    # repo.migrate_states(Path("Users"))
    # user = rr.get_user_state(user_id)
    # print("")

@router_maintenance.message(Command('whatsup'))
async def whatsup(message: Message):
    lines = []
    rows = ReadRepository().get_users_progress()
    for r in rows:
        id = r[0]
        username = r[1]
        filename = r[2].replace('.epub','')
        percent = r[5] or 0

        if filename:
            line = (f"👤{username}:{id} 📖{filename}: {percent}%")
        else:
            line = (f"👤{username}:{id} 📖not read")
        lines.append(line)

    await message.answer("\n".join(lines))


