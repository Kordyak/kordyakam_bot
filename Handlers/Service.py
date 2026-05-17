import os
from pathlib import Path

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from aiogram.filters import Command
from tokenizers.decoders import Replace

from Keyboards.Universal import confirm_kb
from SQL.DB_library import DB_library

router_service = Router(name='maintenance')


# start call_process_by_time
@router_service.message(F.text.regexp(r"^\d{6}$"))
async def run_rdp(message: Message):
    os.system(f"start call_process_by_time.exe {message.text}")
    await message.delete()


@router_service.message(Command("hibernate"))
async def stop_bot(message: Message):
    await message.answer('Вы уверены?', reply_markup=confirm_kb('hibernate'))


@router_service.message(Command("reboot"))
async def stop_bot(message: Message):
    await message.answer('Вы уверены?', reply_markup=confirm_kb('reboot'))


@router_service.message(Command("exit"))
async def stop_bot(message: Message):
    await message.answer('Вы уверены?', reply_markup=confirm_kb('exit'))


@router_service.message(Command("sql"))
async def migration(message: Message):
    await message.answer('Вносим изменения в DB SQL')
    # db = DB_library(Path("SQL/read.db"))
    # repo.migrate_books_index(Path("Books/books_index.json"))
    # repo.migrate_states(Path("Users"))
    # user = db.get_user_state(user_id)
    # print("")

@router_service.message(Command('users'))
async def users(message: Message):
    lines = []
    rows = DB_library().get_users_progress()
    for r in rows:
        id = r[0]
        username = r[1]
        filename = r[2]
        percent = r[5] or 0
        last_access = r[6]
        if filename:
            line = (
                f"\n📡 Last contact: {last_access}"
                f"\n👤 {username}, id: {id}"
                f"\n📖 <code>{filename}</code> {percent}%"
                    )
        else:
            line = (
                f"\n📡 Last access: {last_access}"
                f"\n👤 {username}, id: {id}"
                f"\n📖 Not read"
            )
        lines.append(line)
    await message.answer("\n".join(lines), parse_mode="HTML")


