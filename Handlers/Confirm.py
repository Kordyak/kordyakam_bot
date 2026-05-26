import os

from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery

from Locales.translator import t
from SQL.DB_library import DB_library
from Services.Scheduler import scheduler

router_universal = Router(name='universal')


# Универсальный обработчик подтверждения ==========
@router_universal.callback_query(F.data.startswith("confirm:"))
async def handle_confirm(callback: CallbackQuery, reader, db: DB_library):
    await callback.answer()
    user_id = reader.user_id
    lang = reader.lang_interface
    action = callback.data.split(":")[1]

    if action == "del_book":
        db.remove_current_book(user_id)
        await callback.message.edit_text(t(reader.lang_interface, "book_deleted"))

    elif action == 'remove_daily_time':
        db.remove_daily_time(user_id)
        # Удаляем работу из планировщика
        job_id = f"user_{user_id}"
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)
        await callback.message.edit_text(text=t(lang, 'time_cleared'))


    # SERVICE ========================================================
    elif action == 'hibernate':
        await callback.message.answer("ПК засыпает... 😴")
        os.system(f"shutdown /h")

    elif action == 'reboot':
        await callback.message.answer("Перезагрузка ПК...🏴‍☠")
        os.system(f"shutdown -r -t 0")

    elif action == 'exit':
        await callback.message.answer("Бот выключается...🏴‍☠")
        exit()



# Кнопка отмена
@router_universal.callback_query(F.data == "cancel")
async def cancel_index(callback: CallbackQuery, state: FSMContext):
    await state.set_state(None)
    await callback.answer('Запрос отменен!')
    await callback.message.delete()
