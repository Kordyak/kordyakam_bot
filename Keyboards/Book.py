from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# Главная клавиатура
def book_menu(reader):
    if not reader:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📖 Загрузить свою книгу (.epub)", callback_data="upload_book")],
            [InlineKeyboardButton(text="📚 Библиотека", callback_data="library")],
        ])

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"▶️ Читаем '{reader.book_title}'", callback_data="next_chunk")],
        [InlineKeyboardButton(text=f"📖 Описание '{reader.book_title}'", callback_data="current_book")],
        # [InlineKeyboardButton(text=f"🔄 Загрузить свою книгу (.epub)", callback_data="upload_book")],
        [InlineKeyboardButton(text="📚 Библиотека", callback_data="library")],
        [InlineKeyboardButton(text=f"Прогресс {reader.progress}%, Абзац: №{reader.index}",
                              callback_data="set_paragraf_index")],
        [InlineKeyboardButton(text=f"⏰ График отправки абзаца: {reader.time}", callback_data="change_time")],
        [InlineKeyboardButton(text="❌ Удалить книгу", callback_data="del_book")],
    ])

