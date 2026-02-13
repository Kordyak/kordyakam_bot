from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def main_menu(has_book: bool):

    if not has_book:

        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📚 Загрузить книгу", callback_data="upload_book")]
        ])

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📖 Текущая книга", callback_data="current_book")],
        [InlineKeyboardButton(text="🔄 Заменить книгу", callback_data="replace_book")],
        [InlineKeyboardButton(text="▶ Следующий чанк", callback_data="next_chunk")],
        [InlineKeyboardButton(text="⏰ Время отправки", callback_data="change_time")]
    ])



@router.message(CommandStart())
async def start(message: Message):

    has_book = UserManager.get_book_path(message.from_user.id).exists()

    await message.answer(
        "Я умею читать книги 😈",
        reply_markup=main_menu(has_book)
    )


