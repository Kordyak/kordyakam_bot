import os

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from FSM.states import UploadBook
from SQL.DB_library import DB_library
from Services.Library import Library
from Services.Scheduler import scheduler

router_universal = Router(name='universal')


# Универсальный обработчик подтверждения ==========
@router_universal.callback_query(F.data.startswith("confirm:"))
async def handle_confirm(callback: CallbackQuery, reader):
    await callback.answer()
    db = reader.db
    user_id = reader.user_id
    action = callback.data.split(":")[1]

    if action == "change_time":
        pass

    elif action == "del_book":
        db.remove_current_book(user_id)
        # Удаляем работу из планировщика
        job_id = f"user_{user_id}"
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)
        await callback.message.edit_text("📚 Книга удалена")

    elif action == 'hibernate':
        await callback.message.answer("ПК засыпает... 😴")
        os.system(f"shutdown /h")

    elif action == 'reboot':
        await callback.message.answer("Бот выключается... 🏴‍☠")
        os.system(f"shutdown -r -t 0")

    elif action == 'exit':
        await callback.message.answer("Бот выключается... 🏴‍☠")
        exit()



# Кнопка отмена
@router_universal.callback_query(F.data == "cancel")
async def cancel_index(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    await callback.answer('Запрос отменен!')
    await callback.message.delete()
