import os

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from FSM.states import UploadBook
from SQL.RR_sql import ReadRepository
from Services.Library import Library
from Services.Scheduler import scheduler

universal_router = Router(name='universal')


# Универсальный обработчик подтверждения ==========
@universal_router.callback_query(F.data.startswith("confirm:"))
async def handle_confirm(callback: CallbackQuery, state: FSMContext, user_id, rr: ReadRepository):
    await callback.answer()

    action = callback.data.split(":")[1]

    if action == "change_time":
        pass

    elif action == "del_book":
        rr.remove_current_book(user_id)
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
@universal_router.callback_query(F.data.startswith("cancel:"))
async def handle_cancel(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await state.clear()
    action = callback.data.split(":")[1]
    await callback.message.edit_text("👌Оставляем без изменений")


# Сброс состояния
@universal_router.callback_query(F.data == "cancel_index")
async def cancel_index(callback: CallbackQuery, state: FSMContext):
    await callback.answer('Запрос отменен!')
    await state.clear()
