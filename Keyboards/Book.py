from aiogram.types import (
    InlineKeyboardMarkup,
    InlineKeyboardButton,
    ReplyKeyboardMarkup,
    KeyboardButton,
)
from Services.Reader import Reader


# Главная клавиатура
def reader_menu(reader: Reader):
    return InlineKeyboardMarkup(
        inline_keyboard=[
        [InlineKeyboardButton(text=f'📖 Описание "{reader.book_title}"', callback_data="current_book")],
        [InlineKeyboardButton(text=f"⏰ Задать время / текущ.: {reader.daily_time}", callback_data="change_time")],
        [InlineKeyboardButton(text=f"🏃‍➡️ Задать скорость / текущ.: {reader.reading_speed}%", callback_data="reading_speed")],
        [InlineKeyboardButton(text=f'🔖 Выбрать абзац', callback_data='set_paragraf_index')],
        [InlineKeyboardButton(text=f'❌ Удалить "{reader.book_title}"', callback_data="del_book")],
    ]
    )


def main_menu():
    buttons = [
        [KeyboardButton(text="📚 Библиотека")],
        [KeyboardButton(text="📖 Загрузить свою книгу")],
        [KeyboardButton(text="⚙️ Меню читателя")],
        [KeyboardButton(text="▶️ Читаем следующий абзац")],
    ]
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True
    )

