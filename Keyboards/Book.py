from aiogram.types import InlineKeyboardMarkup,InlineKeyboardButton,ReplyKeyboardMarkup,KeyboardButton
from Services.Reader import Reader


# Главная клавиатура
def reader_menu(reader: Reader):
    return InlineKeyboardMarkup(
        inline_keyboard=[
        [InlineKeyboardButton(text=f'📖 Описание "{reader.book_title}"', callback_data="current_book")],
        [InlineKeyboardButton(text=f'⏰ Изменить время ({reader.daily_time})', callback_data="change_time")],
        [InlineKeyboardButton(text=f'🏃‍➡️ Изменить скорость ({reader.reading_speed})%', callback_data="reading_speed")],
        [InlineKeyboardButton(text=f'🎙️ Изменить голос ({format_voice_name(reader.voice)})', callback_data='voice')],
        [InlineKeyboardButton(text=f'🔖 Читать с другого абзаца', callback_data='set_paragraf_index')],
        [InlineKeyboardButton(text=f'❌ Удалить "{reader.book_title}"', callback_data="del_book")],
    ]
    )

def format_voice_name(voice: str) -> str:
    # ru-RU-SvetlanaNeural → Svetlana
    return voice.split("-")[-1].replace("Neural", "")

def main_menu():
    buttons = [
        [KeyboardButton(text="📚 Библиотека")],
        [KeyboardButton(text="📖 Загрузить свою книгу")],
        [KeyboardButton(text="⚙️ Меню читателя")],
        [KeyboardButton(text="▶️ Читаем следующий абзац")],
    ]
    return ReplyKeyboardMarkup(
        keyboard=buttons,
        resize_keyboard=True,
        one_time_keyboard=True,
    )

def voice_menu_ru():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🇷🇺 Dmitry (RU)", callback_data="voice:ru-RU-DmitryNeural")],
            [InlineKeyboardButton(text="🇷🇺 Pavel (RU)", callback_data="voice:ru-RU-PavelNeural")],
            [InlineKeyboardButton(text="🇷🇺 Svetlana (RU) ⭐", callback_data="voice:ru-RU-SvetlanaNeural")],
        ]
    )

def voice_menu_eng():
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🇺🇸 Guy (EN)", callback_data="voice:en-US-GuyNeural")],
            [InlineKeyboardButton(text="🇺🇸 Andrew (EN)", callback_data="voice:en-US-AndrewNeural")],
            [InlineKeyboardButton(text="🇺🇸 Brian (EN) ⭐", callback_data="voice:en-US-BrianNeural")],
            [InlineKeyboardButton(text="🇬🇧 Sonia (UK)", callback_data="voice:en-GB-SoniaNeural")],
        ]
    )

