from aiogram.types import InlineKeyboardMarkup,InlineKeyboardButton,ReplyKeyboardMarkup,KeyboardButton
from Locales.translator import t
from Services.Reader import Reader




def reader_menu(reader: Reader, lang: str):
    return InlineKeyboardMarkup(
        inline_keyboard=[
        [InlineKeyboardButton(text=t(lang, "btn_book_info", title=reader.book_title), callback_data="current_book")],
        [InlineKeyboardButton(text=t(lang, "btn_change_time", time=reader.daily_time), callback_data="change_time")],
        [InlineKeyboardButton(text=t(lang, "btn_change_speed", speed=reader.reading_speed), callback_data="reading_speed")],
        [InlineKeyboardButton(text=t(lang, "btn_change_voice", voice=format_voice_name(reader.voice)), callback_data='voice')],
        [InlineKeyboardButton(text=t(lang, "btn_change_paragraph"), callback_data='set_paragraf_index')],
        [InlineKeyboardButton(text=t(lang, "btn_delete_book", title=reader.book_title), callback_data="del_book")],
    ]
    )
def format_voice_name(voice: str) -> str:
    return voice.split("-")[-1].replace("Neural", "")



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

