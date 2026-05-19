from aiogram.types import InlineKeyboardMarkup,InlineKeyboardButton
from Locales.translator import t
from Services.Reader import Reader




def reader_menu(reader: Reader, lang):
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
            [InlineKeyboardButton(text="🇺🇸 Brian ♂️ ⭐", callback_data="voice:en-US-BrianNeural")],
            [InlineKeyboardButton(text="🇺🇸 Andrew ♂️", callback_data="voice:en-US-AndrewNeural")],
            [InlineKeyboardButton(text="🇺🇸 Guy ♂️ ⭐", callback_data="voice:en-US-GuyNeural")],
            # [InlineKeyboardButton(text="🇺🇸 Davis ♂️", callback_data="voice:en-US-DavisNeural")], # Не работает
            # [InlineKeyboardButton(text="🇺🇸 Tony ♂️", callback_data="voice:en-US-TonyNeural")], # Не работает
            [InlineKeyboardButton(text="🇺🇸 Aria ♀️", callback_data="voice:en-US-AriaNeural")],
            [InlineKeyboardButton(text="🇺🇸 Jenny ♀️", callback_data="voice:en-US-JennyNeural")],
            [InlineKeyboardButton(text="🇺🇸 Emma ♀️", callback_data="voice:en-US-EmmaNeural")],
            [InlineKeyboardButton(text="🇺🇸 Michelle ♀️", callback_data="voice:en-US-MichelleNeural")],

            [InlineKeyboardButton(text="🇬🇧 Ryan ♂️ ⭐", callback_data="voice:en-GB-RyanNeural")],
            # [InlineKeyboardButton(text="🇬🇧 Thomas ♂️", callback_data="voice:en-GB-ThomasNeural")], # УЖАС
            [InlineKeyboardButton(text="🇬🇧 Sonia ♀️", callback_data="voice:en-GB-SoniaNeural")],
            [InlineKeyboardButton(text="🇬🇧 Libby ♀️ ⭐", callback_data="voice:en-GB-LibbyNeural")],
            # [InlineKeyboardButton(text="🇬🇧 Maisie ♀️", callback_data="voice:en-GB-MaisieNeural")], детский
        ]
    )

