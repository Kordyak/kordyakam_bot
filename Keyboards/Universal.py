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
            InlineKeyboardButton(text="✅ Да", callback_data=f"confirm:{action}"),
            InlineKeyboardButton(text="❌ Нет", callback_data=f"cancel:{action}")
        ]
    ])


def cancel_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel")]
        ]
    )




async def send_typing(bot, chat_id: int):
    try:
        while True:
            await bot.send_chat_action(chat_id, ChatAction.TYPING)
            await asyncio.sleep(4)  # меньше 5 сек, чтобы не пропадал
    except asyncio.CancelledError:
        pass
