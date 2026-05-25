import asyncio

from aiogram.enums import ChatAction
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


# Универсальная клавиатура подтверждения =================================
def confirm_kb(action: str) -> InlineKeyboardMarkup:
    """
    action — короткое имя действия (например: change_time, delete_book)
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ yes", callback_data=f"confirm:{action}"),
            InlineKeyboardButton(text="❌ no", callback_data="cancel")
        ]
    ])


def cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ cancel", callback_data="cancel")]
        ]
    )


