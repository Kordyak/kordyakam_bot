import re

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from aiogram.filters import Command
from fsm.states import UploadBook

from services.reader import Creating_reader, Sender
from services.scheduler_service import SchedulerService

from services.user_manager import UserManager

book_router = Router(name='book')


def main_menu(reader):
    if not reader:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📚 Загрузить книгу", callback_data="upload_book")]
            [InlineKeyboardButton(text="📚 Библиотека книг", callback_data="upload_book")]
        ])

    progress = reader.progress if reader else "0%"

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📖Книга загружена, прочтено:({progress})%", callback_data="current_book")],
        [InlineKeyboardButton(text=f"📖Установить прогресс", callback_data="current_book")],
        [InlineKeyboardButton(text="🔄 Заменить книгу", callback_data="upload_book")],
        [InlineKeyboardButton(text="▶ Отправь мне очередной абзац", callback_data="next_chunk")],
        [InlineKeyboardButton(text="⏰ Время отправки абзаца", callback_data="change_time")],
        [InlineKeyboardButton(text="Удалить подписку на книгу", callback_data="del_subscription")],
    ])


@book_router.message(Command('book'))
async def start(message: Message):
    reader = Creating_reader.get_reader(message.from_user.id)

    text = (
        f"Я @KordyakBot:\n\n"
        "Умею читать книги на английском языке абзацами "
        "по установленному времени или по запросу в формате .epub.\n"
        "Аудио, текст на англ. и скрытый текст на русском.\n\n"
    )
    await message.answer(text,
                         reply_markup=main_menu(reader)
                         )


# Загрузка книги
@book_router.callback_query(F.data == "upload_book")
async def upload_book_start(callback: CallbackQuery, state: FSMContext):
    await callback.answer()  # 🔴 обязательно
    await callback.message.delete()
    await callback.message.answer("Отправь EPUB файл 📚")
    await state.set_state(UploadBook.waiting_epub)


# Загрузка книги
@book_router.message(UploadBook.waiting_epub, F.document)
async def receive_epub(message: Message, bot: Bot, state: FSMContext):
    if not message.document.file_name.endswith(".epub"):
        await message.answer("Это не epub 😅")
        return

    await state.clear()

    user_id = message.from_user.id
    path = UserManager.get_book_path(user_id)
    file = await bot.get_file(message.document.file_id)

    try:
        await bot.download_file(file.file_path, destination=path)
    except Exception as e:
        await message.answer(f"Ошибка при сохранении файла: {e}")
        return

    # ===== RESET ПРОГРЕССА =====
    UserManager.reset_state(user_id)
    # ВАЖНО — очистить cache reader
    Creating_reader.cache.pop(user_id, None)

    await message.answer("Книга загружена 😈")
    await change_time


# Время
@book_router.callback_query(F.data == "change_time")
async def change_time(callback: CallbackQuery, state: FSMContext):
    await callback.answer()  # 🔴 обязательно

    current_time = UserManager.get_time(callback.from_user.id)
    time_text = current_time if current_time else "не задано"

    await callback.message.answer(
        f"⏰ Во сколько отправлять абзац книги?\n"
        f"Сейчас установлено: <b>{time_text}</b>\n\n"
        f"Отправь время в формате <code>HH:MM</code>",
        parse_mode="HTML",
        reply_markup=confirm_kb('change_time')
    )



# Время
@book_router.message(UploadBook.waiting_time)
async def save_time(message: Message, state: FSMContext, sender: Sender):
    time_text = message.text.strip()

    if not re.match(r"^\d{2}:\d{2}$", time_text):
        await message.answer("Формат времени HH:MM 😈")
        return

    user_id = message.from_user.id

    # сохраняем время
    UserManager.save_time(user_id, time_text)

    # 🔥 обновляем scheduler
    sender_service = sender
    SchedulerService.create_user_job(sender_service, user_id, time_text)
    reader = Creating_reader.get_reader(user_id)
    await message.answer(
        f"Время: {time_text} сохранено ✅",
        reply_markup=main_menu(reader)
    )
    await state.clear()


# Текущая книга
@book_router.callback_query(F.data == "current_book")
async def show_book(callback: CallbackQuery):
    id = callback.from_user.id
    reader = Creating_reader.get_reader(id)
    if not reader:
        await  callback.message.answer("Сначала загрузите книгу 📚")
        return

    await callback.message.answer(
        f"📖 {reader.book_author} — {reader.book_title}\n"
        f"Прогресс: {reader.progress}%\n"
        f"Время отправки: {UserManager.get_time(id)}"
    )


@book_router.callback_query(F.data == "next_chunk")
async def next_chunk_handler(callback: CallbackQuery, sender: Sender):
    await callback.answer()
    await sender.send_daily_text(callback.from_user.id)


# Универсальная клавиатура подтверждения
def confirm_kb(action: str):
    """
    action — короткое имя действия (например: change_time, delete_book)
    """
    return InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="✅ Да", callback_data=f"confirm:{action}"),
            InlineKeyboardButton(text="❌ Нет", callback_data=f"cancel:{action}")
        ]
    ])

# Универсальный обработчик подтверждения
@book_router.callback_query(F.data.startswith("confirm:"))
async def handle_confirm(callback: CallbackQuery, state: FSMContext):
    await callback.answer()

    action = callback.data.split(":")[1]

    if action == "change_time":
        await callback.message.edit_text(
            "Отправь время в формате <code>HH:MM</code>",
            parse_mode="HTML"
        )
        await state.set_state(UploadBook.waiting_time)

    elif action == "delete_book":
        # пример будущего действия
        UserManager.delete_book(callback.from_user.id)
        await callback.message.edit_text("📚 Книга удалена")


@book_router.callback_query(F.data.startswith("cancel:"))
async def handle_cancel(callback: CallbackQuery):
    await callback.answer()

    action = callback.data.split(":")[1]

    if action == "change_time":
        reader = Creating_reader.get_reader(callback.from_user.id)
        await callback.message.edit_text(
            "👌 Всё оставляем без изменений",
            reply_markup=main_menu(reader)
        )
