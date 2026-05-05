from aiogram.fsm.state import StatesGroup, State

class UploadBook(StatesGroup):
    waiting_epub = State()
    waiting_paragraph = State()
    waiting_book_number = State()

class StateUser(StatesGroup):
    waiting_reading_speed = State()
    waiting_time = State()
