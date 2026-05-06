from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from Services.Reader import Reader


# Главная клавиатура
def book_menu(reader: Reader):

    if not reader.book_title:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📖 Загрузить свою книгу (.epub)", callback_data="upload_book")],
            [InlineKeyboardButton(text="📚 Библиотека", callback_data="library")],
        ])

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f'▶️ Следующий абзац "{reader.book_title}"', callback_data="next_chunk")],
        [InlineKeyboardButton(text=f'📖 Описание "{reader.book_title}"', callback_data="current_book")],
        # [InlineKeyboardButton(text=f"🔄 Загрузить свою книгу (.epub)", callback_data="upload_book")],
        [InlineKeyboardButton(text="📚 Библиотека", callback_data="library")],
        [InlineKeyboardButton(text=f'🔖 Задать № абзаца, текущий {reader.index}',
                              callback_data='set_paragraf_index')],
        [InlineKeyboardButton(text=f"⏰ Время получения абзаца: {reader.daily_time}", callback_data="change_time")],
        [InlineKeyboardButton(text=f"🏃‍➡️ Задать скорость чтения, текущая {reader.reading_speed}%", callback_data="reading_speed")],
        [InlineKeyboardButton(text=f'❌ Удалить "{reader.book_title}"', callback_data="del_book")],
    ])

