from pathlib import Path

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, BufferedInputFile
from aiogram.filters import Command
from aiogram.enums import ChatAction

from FSM.states import UploadBook
from Keyboards.Book import book_menu
from Keyboards.Universal import confirm_kb, cancel_kb
from Services.BookMetadata import BookMetadata
from Services.Converters import translate_rus_eng
from Services.Library import Library, BOOK_DIR, load_books_index

from Services.Reader import ReaderCache, Sender, Reader
from Services.Scheduler import Scheduler, scheduler

from Services.UserState import UserState

book_router = Router(name='book')



@book_router.message(Command('book'))
async def book_handler(message: Message, state: FSMContext, reader: Reader):
    await state.clear()
    # reader = ReaderCache.get_reader(message.from_user.id)

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
                         reply_markup=book_menu(reader)
                         )


# 📚 Показать библиотеку ================================
@book_router.callback_query(F.data == "library")
async def show_library(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    # await callback.message.delete()

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


# Выбора номера книги из библиотеки
@book_router.message(UploadBook.waiting_book_number)
async def choose_book_from_library(message: Message, state: FSMContext):
    data = await state.get_data()
    book_map = data.get("book_map", {})

    if message.text not in book_map:
        await message.answer("Некорректный номер. Попробуйте снова.")
        return

    book_info = book_map[message.text]
    await state.update_data(book_info=book_info)

    # await book_description(message, book_info)

    # Предлагаем действия
    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"Описание книги '{book_info['book_title']}'", callback_data="book_description")],
            [InlineKeyboardButton(text=f"ℹ️ Загружаем '{book_info['book_title']}' для чтения?",
                                  callback_data=f"upload_library_book:{book_info['path']}")],
            [InlineKeyboardButton(text="🔙 Назад в библиотеку", callback_data="library")],
        ]
    )
    await message.answer(
        f"Что надумал?",
        reply_markup=kb
    )
    # await state.clear()  # очищаем состояние


# Описание книги
@book_router.callback_query(F.data == "book_description")
async def book_description(callback: CallbackQuery, state: FSMContext):
    message = callback.message

    data = await state.get_data()
    book_info = data.get("book_info", {})

    description = book_info['description']
    caption = (
        f"<b>Автор</b>: {book_info['book_creator']}\n"
        f"<b>Книга</b>: {book_info['book_title']}\n"
        f"<b>Описание</b>:\n{description}"
    )

    if book_info['cover_image']:  # если есть байты картинки
        photo = BufferedInputFile(book_info['cover_image'], filename="cover.jpg")
        await message.answer_photo(photo=photo, caption=caption, parse_mode="HTML")
    else:
        await message.answer(caption)

    # Описание на русском
    description_ru = translate_rus_eng(description, "/en_ru")
    await message.answer(
        text=f"<tg-spoiler>{description_ru}</tg-spoiler>",
        parse_mode="HTML",
    )


    # kb = InlineKeyboardMarkup(
    #     inline_keyboard=[
    #         [InlineKeyboardButton(text=f"ℹ️ Загружаем '{book_info['book_title']}' для чтения?",
    #                               callback_data=f"upload_library_book:{book_info['path']}")],
    #         [InlineKeyboardButton(text="🔙 Назад в библиотеку", callback_data="library")],
    #     ]
    # )
    # await message.answer('Что надумал?', reply_markup=kb)
    # await message.delete()
    await state.clear()  # очищаем состояние


# Загрузка своей книги КОЛБЭК
@book_router.callback_query(F.data == "upload_book")
async def upload_book_start(callback: CallbackQuery, state: FSMContext):
    await callback.answer()  # 🔴 обязательно
    await callback.message.answer("Отправь свой EPUB файл 📚 для загрузки")
    await state.set_state(UploadBook.waiting_epub)


# Загрузка своей книги waiting_epub
@book_router.message(UploadBook.waiting_epub, F.document)
async def upload_book_wait(message: Message, bot: Bot, state: FSMContext, user_id):

    if not message.document.file_name.endswith(".epub"):
        await message.answer(
            'Это не epub 😅',
            reply_markup=cancel_kb()
        )
        return

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


# Загрузка книги из библиотек (КОЛБЭК)
@book_router.callback_query(F.data.startswith("upload_library_book:"))
async def upload_library_book(callback: CallbackQuery, state: FSMContext, user_id):
    await callback.answer()
    # await callback.message.delete()
    path = callback.data.split(":")[1]
    await upload_book_end(callback.message, user_id, path, state)


# Загрузка книги КОНЕЦ // ФУНКЦИЯ из библ / или своя загруженная
async def upload_book_end(message, user_id, path, state):
    # Создаем состояние для user
    UserState.reset_state(user_id, path)
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
    current_time = UserState.get_time(callback.from_user.id)
    time_text = current_time if current_time else "не задано"

    await callback.message.edit_text(
        f"⏰Сейчас время отправки абзаца: <b>{time_text}</b>.\n"
        f"Изменить время?",
        parse_mode="HTML",
        reply_markup=confirm_kb('change_time')
    )


# Задаем Время
@book_router.message(UploadBook.waiting_time)
async def save_time(message: Message, state: FSMContext, sender: Sender, user_id):
    time_text = message.text.strip()

    try:
        hours, minutes = map(int, time_text.split(":"))
        if not (0 <= hours <= 23 and 0 <= minutes <= 59):
            raise ValueError
    except:
        await message.answer(
            'Некорректное время. Формат HH:MM 😈',
            reply_markup=cancel_kb()
        )
        return

    # user_id = message.from_user.id

    # сохраняем время
    UserState.save_time(user_id, time_text)
    # Кэш чтеца удаляем из памяти
    ReaderCache.cache.pop(user_id, None)
    reader = ReaderCache.get_reader(user_id)

    # 🔥 обновляем scheduler
    sender_service = sender
    Scheduler.create_user_job(sender_service, user_id, time_text)

    await message.answer(f"Время: {time_text} установлено, планировщик включен ✅",
                         reply_markup=book_menu(reader))
    await state.clear()


# Информация о текущей книги
@book_router.callback_query(F.data == "current_book")
async def show_book(callback: CallbackQuery, state: FSMContext, reader: Reader):
    await callback.answer()

    if not reader:
        await callback.answer("Сначала загрузите книгу 📚")
        return

    book_info = {
        'book_title': reader.book_title,
        'book_creator': reader.book_creator,
        'description': reader.description,
        'cover_image': reader.cover_image,
        'path': reader.book_path,
    }
    await state.update_data(book_info=book_info)

    await book_description(callback, state)


# Отправить ЧАНК
@book_router.callback_query(F.data == "next_chunk")
async def next_chunk_handler(callback: CallbackQuery, sender: Sender, user_id):
    await callback.answer()
    temp_msg = await callback.message.edit_text("Готовим абзац книги...")
    chat_id = callback.message.chat.id
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
async def save_index(message: Message, state: FSMContext, user_id, reader: Reader):
    if not reader:
        await message.answer("Книга не найдена!")
        await state.clear()
        return

    if not message.text.isdigit():
        await message.answer(
            'Укажите № абзаца от которого начнем читать',
            reply_markup=cancel_kb()
        )
        return

    index = int(message.text)
    if index < 0 or index > reader.index_all:
        await message.answer(
            f"Введите число от 0 до {reader.index_all}",
            reply_markup=cancel_kb()
        )
        return

    UserState.save_index(user_id, index)
    ReaderCache.cache.pop(user_id, None)
    reader = ReaderCache.get_reader(user_id)

    await message.answer("✅ Индекс абзаца обновлён!",reply_markup=book_menu(reader))
    await state.clear()


# Удалить книгу
@book_router.callback_query(F.data == 'del_book')
async def del_book(callback: CallbackQuery):
    await callback.answer()
    await callback.message.answer('Вы уверены?', reply_markup=confirm_kb('del_book'))


