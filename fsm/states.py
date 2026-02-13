from aiogram.fsm.state import StatesGroup, State

class UploadBook(StatesGroup):
    waiting_confirm = State()
    waiting_time = State()