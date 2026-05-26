from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

from Locales.translator import t


# Универсальная клавиатура подтверждения =================================
def confirm_kb(action: str, lang: str = None) -> InlineKeyboardMarkup:
    """
    action — короткое имя действия (например: change_time, delete_book)
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text=t(lang,'btn_yes'), callback_data=f"confirm:{action}"),
            InlineKeyboardButton(text=t(lang,'btn_no'), callback_data="cancel")
        ]
    ])


def cancel_kb(lang) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang,'btn_cancel'), callback_data="cancel")]
        ]
    )


