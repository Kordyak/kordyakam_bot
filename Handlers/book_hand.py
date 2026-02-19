from pathlib import Path

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, BufferedInputFile
from aiogram.filters import Command
from aiogram.enums import ChatAction

from FSM.states import UploadBook
from Services.BookMetadata import BookMetadata
from Services.Library import Library, BOOK_DIR, load_books_index

from Services.Reader import ReaderCache, Sender, Reader
from Services.Scheduler import Scheduler, scheduler

from Services.StateUser import StateUser

book_router = Router(name='book')


def main_menu(reader):
    if not reader:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📖 Загрузить книгу", callback_data="upload_book")],
            [InlineKeyboardButton(text="📚 Библиотека", callback_data="library")],
        ])

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📖 Загружена книга {reader.book_title}, информация", callback_data="current_book")],
        [InlineKeyboardButton(text=f"🔄 Заменить книгу", callback_data="upload_book")],
        [InlineKeyboardButton(text="📚 Библиотека", callback_data="library")],
        [InlineKeyboardButton(text=f"#️⃣ № последнего прочитанного абзаца: {reader.index}", callback_data="set_paragraf_index")],
        [InlineKeyboardButton(text="▶️ Читаем далее", callback_data="next_chunk")],
        [InlineKeyboardButton(text=f"⏰ Время отправки абзаца: {reader.time}", callback_data="change_time")],
        [InlineKeyboardButton(text="❌ Удалить книгу", callback_data="del_book")],
    ])


@book_router.message(Command('book'))
async def book_handler(message: Message):
    reader = ReaderCache.get_reader(message.from_user.id)

    if not reader:

        text = (
            f"Я @KordyakBot:\n\n"
            "Умею читать книги на английском языке абзацами "
            "по установленному времени или по запросу в формате .epub.\n"
            "Отправляю вам аудио, текст на англ. и скрытый текст на русском.\n\n"
            "Вам необходимо загрузить книгу на англ. в формате .epub.\n"
        )
    else:
        text = f'Привет мой друг, продолжаем читать книгу {reader.book_title}\n'

    await message.answer(text,
                         reply_markup=main_menu(reader)
                         )


# 📚 Показать библиотеку ================================
@book_router.callback_query(F.data == "library")
async def show_library(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.delete()

    books_index = load_books_index()
    if not books_index:
        await callback.message.answer("В библиотеке пока нет книг 📚")
        return

    # Формируем пронумерованный список с актуальными метаданными
    book_list_text = "📚 Библиотека:\n\n"
    book_map = {}  # номер → hash

    for i, (file_hash, info) in enumerate(books_index.items(), start=1):
        book_path = BOOK_DIR / info["filename"]

        metadata = BookMetadata.get_cache(book_path)
        title = metadata["book_title"]
        creator = metadata["book_creator"]
        description = metadata["description"]
        cover_image = metadata["cover_image"]

        book_list_text += f"{i}. {title} ({creator})\n"

        book_map[str(i)] = {
            'book_title': title,
            'book_creator': creator,
            'description': description,
            'cover_image': cover_image,
            'path': book_path,
        }

    # Сохраняем mapping в state
    await state.update_data(book_map=book_map)

    await callback.message.answer(
        book_list_text + "\nНапишите номер книги, чтобы выбрать её для чтения или просмотра информации."
    )

    await state.set_state(UploadBook.waiting_book_number)


# Шаг 2: обработка выбора номера книги
@book_router.message(UploadBook.waiting_book_number)
async def choose_book_by_number(message: Message, state: FSMContext):
    data = await state.get_data()
    book_map = data.get("book_map", {})

    if message.text not in book_map:
        await message.answer("Некорректный номер. Попробуйте снова.")
        return

    book_info = book_map[message.text]

    await msg_book_info(message, book_info)

    # Предлагаем действия
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="ℹ️ Загружаем эту книгу?",
                                  callback_data=f"upload_book_end:{book_info['path']}")],
            [InlineKeyboardButton(text="🔙 Назад в библиотеку", callback_data="library")],
        ]
    )

    await message.answer(
        f"Что надумал мой дружок?",
        reply_markup=kb
    )

    await state.clear()  # очищаем состояние


async def msg_book_info(message, book_info):
    caption = (
        f"Автор: {book_info['book_creator']}\n"
        f"Книга: {book_info['book_title']}\n"
        f"\nОписание книги:\n{book_info['description']}"
    )

    if book_info['cover_image']:  # если есть байты картинки
        photo = BufferedInputFile(book_info['cover_image'], filename="cover.jpg")
        await message.answer_photo(photo=photo, caption=caption)
    else:
        await message.answer(caption)


# ================
# Загрузка книги
# ================
@book_router.callback_query(F.data == "upload_book")
async def upload_book_start(callback: CallbackQuery, state: FSMContext):
    await callback.answer()  # 🔴 обязательно
    await callback.message.delete()
    await callback.message.answer("Отправь EPUB файл 📚")
    await state.set_state(UploadBook.waiting_epub)


# Загрузка книги waiting_epub
@book_router.message(UploadBook.waiting_epub, F.document)
async def upload_book_wait(message: Message, bot: Bot, state: FSMContext):
    if not message.document.file_name.endswith(".epub"):
        await message.answer("Это не epub 😅")
        return

    user_id = message.from_user.id

    await state.clear()

    original_name = message.document.file_name
    temp_path = BOOK_DIR / f"temp_{user_id}.epub"

    file = await bot.get_file(message.document.file_id)

    try:
        await bot.download_file(file.file_path, destination=temp_path)
    except Exception as e:
        await message.answer(f"Ошибка при сохранении файла: {e}")
        return

    file_hash = Library.calculate_hash(temp_path)
    books_index = load_books_index()

    # 🔎 Если уже есть по хэшу
    if file_hash in books_index:
        existing_name = Path(books_index[file_hash]["filename"])
        final_path = BOOK_DIR / existing_name
        temp_path.unlink()
        await message.answer("Такая книга уже есть в моей базе 📚")

    else:  # 📥 Если новая книга
        final_path = BOOK_DIR / original_name
        counter = 1
        while final_path.exists():
            final_path = BOOK_DIR / f"{Path(original_name).stem}_{counter}.epub"
            counter += 1
        temp_path.rename(final_path)
        # сохраняем книгу в books_index
        Library.add_book(final_path)

    await upload_book_end(message, user_id, final_path, state)


# Загрузка книги КОНЕЦ
@book_router.callback_query(F.data.startswith("upload_book_end:"))
async def upload_book_end_callback(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    path = callback.data.split(":")[1]
    await upload_book_end(callback.message, callback.from_user.id, path, state)


async def upload_book_end(message, user_id, path, state):
    # Создаем состояние для user
    StateUser.reset_state(user_id, path)
    # Сбрасываем кэш reader если есть
    ReaderCache.cache.pop(user_id, None)
    reader = ReaderCache.get_reader(user_id)
    await message.answer(f"Книга {reader.book_title} установлена.\n"
                         "Сейчас давайте установим время отправки абзаца на каждый день.\n"
                         "Укажите время в формате HH:MM")
    await state.set_state(UploadBook.waiting_time)


# Задаем Время ================================
@book_router.callback_query(F.data == "change_time")
async def change_time(callback: CallbackQuery):
    await callback.answer()  # 🔴 обязательно

    current_time = StateUser.get_time(callback.from_user.id)
    time_text = current_time if current_time else "не задано"

    await callback.message.edit_text(
        f"⏰Сейчас время отправки абзаца: <b>{time_text}</b>.\n"
        f"Изменить время?",
        parse_mode="HTML",
        reply_markup=confirm_kb('change_time')
    )


# Задаем Время
@book_router.message(UploadBook.waiting_time)
async def save_time(message: Message, state: FSMContext, sender: Sender):
    time_text = message.text.strip()

    try:
        hours, minutes = map(int, time_text.split(":"))
        if not (0 <= hours <= 23 and 0 <= minutes <= 59):
            raise ValueError
    except:
        await message.answer("Некорректное время. Формат HH:MM 😈")
        return

    user_id = message.from_user.id

    # сохраняем время
    StateUser.save_time(user_id, time_text)

    # 🔥 обновляем scheduler
    sender_service = sender
    Scheduler.create_user_job(sender_service, user_id, time_text)
    ReaderCache.cache.pop(user_id, None)
    reader = ReaderCache.get_reader(user_id)
    await message.answer(f"Время: {time_text} установлено, планировщик включен ✅",
                         reply_markup=main_menu(reader))
    await state.clear()


# Информация о текущей книги
@book_router.callback_query(F.data == "current_book")
async def show_book(callback: CallbackQuery):
    await callback.answer()
    # await callback.message.delete()
    user_id = callback.from_user.id
    reader = ReaderCache.get_reader(user_id)

    if not reader:
        await  callback.answer("Сначала загрузите книгу 📚")
        return

    caption = (
        f"Автор: {reader.book_author}\n"
        f"Книга: {reader.book_title}\n"
        f"Прогресс вашего чтения: {reader.progress}%\n"
        f"Номер последнего отправленного абзаца: №{reader.index}\n"
        f"Время отправки абзаца: {StateUser.get_time(callback.from_user.id)}\n"
        f"\nОписание книги:\n{reader.description}"
    )

    if reader.cover:  # если есть байты картинки
        photo = BufferedInputFile(reader.cover, filename="cover.jpg")
        await callback.message.answer_photo(photo=photo, caption=caption)
    else:
        await callback.answer(caption)


# Отправить ЧАНК
@book_router.callback_query(F.data == "next_chunk")
async def next_chunk_handler(callback: CallbackQuery, sender: Sender):
    await callback.answer()
    temp_msg = await callback.message.answer("Готовим абзац книги...")

    user_id = callback.from_user.id
    chat_id = callback.message.chat.id

    # Удаляем старое меню
    # await callback.message.delete()

    # Показываем typing
    await callback.bot.send_chat_action(
        chat_id=chat_id,
        action=ChatAction.TYPING
    )

    try:
        await sender.send_daily_text(user_id)
    finally:
        # Удалится даже если будет ошибка
        await temp_msg.delete()


# установить номер абзаца ================================
@book_router.callback_query(F.data == 'set_paragraf_index')
async def change_index(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.delete()
    await callback.message.answer('Укажите № абзаца от которого начнем читать')
    await state.set_state(UploadBook.waiting_index)


# установить номер абзаца
@book_router.message(UploadBook.waiting_index)
async def save_index(message: Message, state: FSMContext):
    user_id = message.from_user.id
    reader = ReaderCache.get_reader(user_id)

    if not reader:
        await message.answer("Книга не найдена")
        await state.clear()
        return

    if not message.text.isdigit():
        await message.answer("Введите число")
        return

    index = int(message.text)

    if index < 0 or index > reader.index_all:
        await message.answer(
            f"Введите число от 0 до {reader.index_all}"
        )
        return

    StateUser.save_index(user_id, index)

    ReaderCache.cache.pop(user_id, None)
    reader = ReaderCache.get_reader(user_id)

    await message.answer("✅ Индекс обновлён!", reply_markup=main_menu(reader))
    await state.clear()


# Удалить книгу
@book_router.callback_query(F.data == 'del_book')
async def del_book(callback: CallbackQuery):
    await callback.answer()
    await callback.message.edit_text('Вы уверены?', reply_markup=confirm_kb('del_book'))


# ================================
# Универсальная клавиатура подтверждения
# ================================
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
    user_id = callback.from_user.id
    await callback.answer()

    action = callback.data.split(":")[1]

    if action == "change_time":
        await callback.message.edit_text(
            "Отправь время в формате <code>HH:MM</code>",
            parse_mode="HTML"
        )
        await state.set_state(UploadBook.waiting_time)

    elif action == "del_book":
        # Сбрасываем состояния user в файле STATE
        StateUser.reset_state(user_id, "")
        # Удаляем кэш reader если есть
        ReaderCache.cache.pop(user_id, None)
        # Удаляем работу из планировщика
        job_id = f"user_{user_id}"
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)
        await callback.message.edit_text("📚 Книга удалена")


@book_router.callback_query(F.data.startswith("cancel:"))
async def handle_cancel(callback: CallbackQuery):
    await callback.answer()
    action = callback.data.split(":")[1]

    if action == "change_time":
        reader = ReaderCache.get_reader(callback.from_user.id)
        await callback.message.edit_text(
            "👌 Время оставляем без изменений",
            reply_markup=main_menu(reader)
        )

    await callback.message.edit_text("👌Оставляем без изменений")
