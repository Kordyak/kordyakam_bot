from contextlib import suppress
from html import unescape
from pathlib import Path
import re

from aiogram import Router, F, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, BufferedInputFile
from aiogram.filters import Command

from FSM.states import UploadBook, StateUser
from Keyboards.Book import reader_menu, main_menu
from Keyboards.Universal import confirm_kb, cancel_kb
from SQL.DB_library import DB_library
from Services.BookMetadata import BookMetadata
from Services.Converters import translator
from Services.Library import Library, PATH_BOOKS, epub_paragraph_generator

from Services.Reader import Sender, Reader


router_book = Router(name='book')


@router_book.message(Command('start'))
async def run_rdp(message: Message, reader: Reader, state: FSMContext):
    await state.clear()

    if not reader.book_title:
        text = (
            f'Привет, <b>{message.from_user.first_name}</b>!'
            f"\nДавай выберем <b>книгу из моей библиотеки</b> или можешь загрузить <b>свою</b> в формате <b>.epub</b>."
            f"\nДля этого используй <b>пользовательскую панель</b> внизу, вызывается <b>кнопкой в правом нижнем углу</b>."
        )
    else:
        text = (
            f"Привет, <b>{message.from_user.first_name}</b>!"
            f'\nПохоже ты еще читаешь <b>"{reader.book_title}"</b>.'
            f'\nТы можешь через <b>пользовательскую панель</b> под чатом проверить <b>свое состояние</b> или вызвать <b>новый абзац</b>'
        )
    await message.answer(
        text,
        parse_mode="HTML",
        reply_markup=main_menu(),
    )


@router_book.message(F.text == "⚙️ Меню читателя")
async def book_handler(message: Message, reader: Reader, state: FSMContext):
    # await state.set_state(None)
    if not reader.book_title:
        await message.answer(
                            f"Похоже у тебя не загружена книга.\nВыбери из библиотеки или загрузи свою в формате epub",
                            )
    else:
        text = (f'Меню читателя:'
                f'\nСейчас вы читаете: <b>"{reader.book_title}"</b>'
                f'\nПоследний абзац: <b>{reader.paragraph_indx}</b>'
                f'\nВаш прогресс чтения: <b>{reader.progress}%</b>'
                )
        await message.answer(
                            text,
                            reply_markup=reader_menu(reader),
                            parse_mode='HTML'
                            )


# ================= 📚 Библиотека ========================
@router_book.message(F.text =="📚 Библиотека")
async def show_library(message: Message, state: FSMContext):
    books_index = DB_library().list_books()  # {hash: {filename, total_paragraphs}}

    if not books_index:
        await message.answer("В библиотеке пока нет книг 📚")
        return

    # Собираем книги в список
    books = []

    for file_hash, info in books_index.items():
        book_path = PATH_BOOKS / info["filename"]

        metadata = BookMetadata.get_cache(book_path)

        books.append({
            "hash": file_hash,
            "title": metadata.get("book_title", info["filename"]),
            "creator": metadata.get("book_creator", "Неизвестен"),
            "description": metadata.get("description", ""),
            "cover_image": metadata.get("cover_image", b""),
            "info": info
        })

    # Сортировка по автору
    books.sort(key=lambda x: x["creator"].lower())

    # Формируем текст и map
    books_list = []
    books_map = {}

    for i, book in enumerate(books, start=1):
        books_list.append(
            f"{i}. {book['creator']} / <b>{book['title']}</b>"
        )

        books_map[str(i)] = {
            "title": book["title"],
            "creator": book["creator"],
            "description": book["description"],
            "cover_image": book["cover_image"],
            "filename": book["info"]["filename"],
            "hash": book["hash"],
            "total_paragraphs": book["info"].get("total_paragraphs", 0),
        }

    msg = "📚 Библиотека:\n\n"
    msg += "\n".join(books_list)
    msg += "\n\nНапишите номер книги, чтобы выбрать её для чтения или просмотра информации."

    await send_long_message(message, msg)
    await state.update_data(books_map=books_map)# сохранить в state
    await state.set_state(UploadBook.waiting_book_number)
# если длинное сообщение, делим на 4096
async def send_long_message(message, text: str):
    max_message_length = 4096
    current = ""

    for line in text.split("\n"):
        if len(current) + len(line) + 1 > max_message_length:
            await message.answer(current, parse_mode='HTML')
            current = line
        else:
            current += "\n" + line if current else line

    if current:
        await message.answer(current, parse_mode='HTML')
# Выбора номера книги из библиотеки
@router_book.message(UploadBook.waiting_book_number)
async def choose_book_from_library(message: Message, state: FSMContext):
    data = await state.get_data()
    books_map = data.get("books_map", {})
    i = message.text

    if i not in books_map:
        await message.answer(
            text="Некорректный номер книги. Чтобы выйти, жми отмена.",
            reply_markup=cancel_kb()
        )
        return

    book = books_map[i]
    await state.update_data(book_info=book)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=f"ℹ️ Описание книги",callback_data="book_description")],
            [InlineKeyboardButton(text=f"⬇️ Загружаем книгу для чтения?",callback_data=f"upload_library_book:{i}")]
        ]
    )
    await message.answer(
        f"Вы выбрали:"
        f"\n{i}. {book['creator']} / <b>{book['title']}</b>"
        f"\nИли выберите другую книгу, указав другой номер книги.",
        reply_markup=kb,
        parse_mode = 'HTML'
    )
# Описание книги
@router_book.callback_query(F.data == "book_description")
async def book_description(callback: CallbackQuery, state: FSMContext):
    message = callback.message

    data = await state.get_data()
    book_info = data.get("book_info", {})
    description = book_info['description']

    caption = (
        f"<b>Author</b>: {book_info['creator']}\n"
        f"<b>Book</b>: {book_info['title']}\n"
        f"<b>Total paragraphs</b>: {book_info['total_paragraphs']}"
        f"\n{description}"
    )

    if book_info['cover_image']:  # если есть байты картинки
        photo = BufferedInputFile(book_info['cover_image'], filename="cover.jpg")
        await message.answer_photo(photo=photo, caption=caption, parse_mode="HTML")
    else:
        await message.answer(caption)

    # Описание на русском
    description_ru = await translator(description)
    await message.answer(
        text=f"<tg-spoiler>{description_ru}</tg-spoiler>",
        parse_mode="HTML",
    )




# Описание текущей книги
@router_book.callback_query(F.data == "current_book")
async def current_book(callback: CallbackQuery, state: FSMContext, reader: Reader):
    await callback.answer()
    if not reader:
        await callback.answer("Сначала загрузите книгу 📚")
        return

    book_info = {
        'title': reader.book_title,
        'creator': reader.book_creator,
        'description': reader.description,
        'cover_image': reader.cover_image,
        'path': reader.book_name,
        'total_paragraphs': reader.total_paragraphs,
    }
    await state.update_data(book_info=book_info)
    await book_description(callback, state)





# Загрузка книги из библиотек
@router_book.callback_query(F.data.startswith("upload_library_book:"))
async def upload_library_book(callback: CallbackQuery, state: FSMContext, user_id, db: DB_library):
    await callback.answer()
    i = callback.data.split(":")[1]
    data = await state.get_data()
    books_map = data.get("books_map", {})
    file_name = books_map[i]['filename']
    await upload_book(callback.message, user_id, file_name, state, db)


# Загрузка собственной книги
@router_book.message(F.text == "📖 Загрузить свою книгу")
async def upload_my_book(message: Message, state: FSMContext):
    await message.answer("Отправь свой EPUB файл 📚 для загрузки")
    await state.set_state(UploadBook.waiting_epub)
@router_book.message(UploadBook.waiting_epub, F.document)
async def upload_my_book_waiting(message: Message, bot: Bot, state: FSMContext, user_id, db: DB_library):
    if not message.document.file_name.endswith(".epub"):
        await message.answer(
            'Это не epub 😅',
            reply_markup=cancel_kb()
        )
        return

    original_name = message.document.file_name
    temp_path = PATH_BOOKS / f"temp_{user_id}.epub"
    file = await bot.get_file(message.document.file_id)

    try:
        await bot.download_file(file.file_path, destination=temp_path)
    except Exception as e:
        await message.answer(f"Ошибка при сохранении файла: {e}")
        await state.set_state(None)
        return

    # Вычисляем hash загруженной книги
    library = Library()
    file_hash = library.calculate_hash(temp_path)
    books_index = DB_library().list_books() # возвращает {hash: {filename, total_paragraphs}}

    # 🔎 Если уже есть по хэшу
    if file_hash in books_index:
        final_name = Path(books_index[file_hash]["filename"])
        temp_path.unlink()
        await message.answer("Такая книга уже есть в моей базе 📚")

    else:  # 📥 Если новая книга
        final_name = PATH_BOOKS / original_name
        counter = 1
        while final_name.exists():
            final_name = PATH_BOOKS / f"{Path(original_name).stem}_{counter}.epub"
            counter += 1
        temp_path.rename(final_name)
        # сохраняем книгу в books_index
        library.add_book(final_name)
    await upload_book(message, user_id, final_name, state, db)
    await state.set_state(None)


# Загрузка книги
async def upload_book(message, user_id, name_file, state: FSMContext, db: DB_library):
    book_path = Path(PATH_BOOKS / name_file)
    file_hash = Library.calculate_hash(book_path)
    # Проверяем, есть ли книга в библиотеке
    book = db.get_book_by_hash(file_hash)
    if not book:
        # Получаем количество абзацев
        total_paragraphs = sum(1 for _ in epub_paragraph_generator(book_path))
        # Добавляем книгу в библиотеку
        book_id = db.add_book(str(name_file), file_hash, total_paragraphs)
    else:
        book_id = book["id"]
    # Назначаем книгу пользователю
    db.set_current_book(user_id, book_id)
    # Создаем Reader для пользователя
    reader = Reader(user_id)
    await message.answer(
        f"Книга {reader.book_title} установлена.\n"
        "Сейчас давайте установим время отправки абзаца на каждый день.\n"
        "Укажите время в формате HH:MM"
    )
    await state.set_state(StateUser.waiting_time)


# Задаем Время
@router_book.callback_query(F.data == "change_time")
async def change_time(callback: CallbackQuery, db: DB_library, user_id: int, state: FSMContext):
    await callback.answer()  # 🔴 обязательно
    time = db.get_time(user_id)
    await callback.message.edit_text(
        f"⏰ Сейчас время отправки абзаца: <b>{time}</b>.\n"
        "Чтобы изменить:\n"
        "отправьте время в формате <code>HH:MM</code>",
        parse_mode="HTML",
    )
    await state.set_state(StateUser.waiting_time)
@router_book.message(StateUser.waiting_time)
async def save_time(message: Message, state: FSMContext, user_id, db: DB_library):
    time = message.text.strip()
    try:
        hours, minutes = map(int, time.split(":"))
        if time.count(":") != 1:
            raise ValueError
        elif not (0 <= hours <= 23 and 0 <= minutes <= 59):
            raise ValueError
    except ValueError:
        await message.answer(
            '😈 Некорректное время. Формат <b>HH:MM</b> ',
            parse_mode="HTML",
            reply_markup=cancel_kb()
        )
        return
    # сохраняем время
    db.save_time(user_id, time)
    await message.answer(
        f"⏰ Установлено время отправки абзаца: <b>{time}</b>"
         f"\nПланировщик включен ✅"
         f"\nА также через <b>пользовательскую клавиатуру под чатом</b> можешь запросить абзац книги, установить скорость чтения...",
         parse_mode = "HTML"
         )
    await state.set_state(None)


# Задаем скорость чтения
@router_book.callback_query(F.data == "reading_speed")
async def change_reading_speed(callback: CallbackQuery, db: DB_library, user_id: int, state: FSMContext):
    await callback.answer()
    reading_speed = db.get_reading_speed(user_id)
    await callback.message.edit_text(
        f"🏃‍➡️ Сейчас для вас установлена скорость чтения <code>{reading_speed}</code>\n"
        f"Вы можете уменьшить либо увеличить скорость от 50 до 150 (диапазон разборчивости)",
        parse_mode="HTML"
    )
    await state.set_state(StateUser.waiting_reading_speed)
@router_book.message(StateUser.waiting_reading_speed)
async def save_reading_speed(message: Message, state: FSMContext, user_id: int, db: DB_library):
    try:
        speed = int(message.text.strip())
        if speed < 50:
            speed = 50
        elif speed > 150:
            speed = 150
    except ValueError:
        await message.answer(
            '😈 Вероятно ввели буквы. Формат от 50 до 150 ',
            reply_markup=cancel_kb()
        )
        return
    db.save_reading_speed(user_id, speed)
    await message.answer(
        f"🏃‍➡️ Скорость чтения изменена: {speed}%"
    )
    await state.clear()


# Выбрать абзац
@router_book.callback_query(F.data == 'set_paragraf_index')
async def change_index(callback: CallbackQuery, state: FSMContext, reader: Reader):
    await callback.answer()
    await callback.message.delete()
    await callback.message.answer("Укажите № абзаца c которого начнем читать\n"
                                  f"Введите число от 1 до {reader.total_paragraphs}")
    await state.set_state(UploadBook.waiting_paragraph)
@router_book.message(UploadBook.waiting_paragraph)
async def save_index(message: Message, state: FSMContext, user_id, reader: Reader, db: DB_library, sender: Sender):
    if not reader:
        await message.answer("Книга не найдена!")
        await state.set_state(None)
        return

    if not message.text.isdigit():
        await message.answer(
            f"Укажите число, без текста",
            reply_markup=cancel_kb()
        )
        return

    index = int(message.text) - 1

    if index < 0 or index > reader.total_paragraphs:
        await message.answer(
            f"Введите число в диапазоне от 1 до {reader.total_paragraphs}",
            reply_markup=cancel_kb()
        )
        return

    db.save_i_chunk(user_id, index)

    await message.answer("✅ Индекс абзаца обновлён!")
    await next_chunk(message, sender, user_id, Reader(user_id), state)
    await state.set_state(None)


# Читаем следующий абзац
@router_book.message(F.text == "▶️ Читаем следующий абзац")
async def next_chunk(message: Message, sender: Sender, user_id: int,  reader: Reader, state: FSMContext):
    if not reader.book_title:
        await book_handler(message, reader, state)
        return

    msg = await message.answer(f"Готовим абзац ...")
    try:
        await sender.send_chunk(user_id, reader)
    finally:
        with suppress(TelegramBadRequest):
            await msg.delete()


# Удалить книгу
@router_book.callback_query(F.data == 'del_book')
async def del_book(callback: CallbackQuery):
    await callback.answer()
    await callback.message.delete()
    await callback.message.answer('Вы уверены?', reply_markup=confirm_kb('del_book'))
