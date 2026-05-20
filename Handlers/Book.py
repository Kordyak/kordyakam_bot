from contextlib import suppress
from io import BytesIO
import re


from aiogram import Router, F, Bot
from aiogram.exceptions import TelegramBadRequest
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, BufferedInputFile
from aiogram.filters import Command
from FSM.states import UploadBook, StateUser
from Keyboards.Book import reader_menu, voice_menu_ru, voice_menu_eng, format_voice_name
from Keyboards.Universal import confirm_kb, cancel_kb
from Locales.translator import t
from SQL.DB_library import DB_library
from Services.BookMetadata import BookMetadata
from Services.Converters import translator, detect_lang_simple
from Services.Library import Library, PATH_EN_BOOKS, epub_paragraph_generator
from Services.Reader import Reader
from Services.Sender import Sender


router_book = Router(name='book')



@router_book.message(Command('start'))
async def start_handler(message: Message, reader: Reader):
    lang = reader.lang_interface
    if not reader.book_title:
        text = t(lang, "start_no_book", first_name=message.from_user.first_name)
        await message.answer(
                            text,
                            parse_mode='HTML'
                            )
    else:
        text =  t(lang, "start_with_book",
                  book_title=reader.book_title,
                  paragraph_indx=reader.paragraph_indx,
                  progress=reader.progress,
                  )
        await message.answer(
                            text,
                            reply_markup=reader_menu(reader, lang),
                            parse_mode='HTML'
                            )


# ================= 📚 Библиотека ========================
@router_book.message(Command("library_en"))
async def show_library(message: Message, state: FSMContext, reader: Reader):
    library = Library()
    library.sync_library()
    lang = reader.lang_interface
    books_index = DB_library().list_books()  # {hash: {filename, total_paragraphs}}

    if not books_index:
        await message.answer(t(lang,'library_empty'))
        return

    # Собираем книги в список
    books = []

    for file_hash, info in books_index.items():
        book_path = PATH_EN_BOOKS / info["filename"]

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

    msg = "\n".join(books_list)
    msg += t(lang,'library_choose')

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




# НОМЕР КНИГИ / Описание или загрузка книги
@router_book.message(UploadBook.waiting_book_number)
async def handler_waiting_book_number(message: Message, state: FSMContext, reader):
    lang = reader.lang_interface
    data = await state.get_data()
    books_map = data.get("books_map", {})
    i = message.text

    if i not in books_map:
        await message.answer(
            text=t(lang,'invalid_book_number'),
            reply_markup=cancel_kb()
        )
        return

    book = books_map[i]
    await state.update_data(book_info=book)

    kb = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=t(lang,'btn_book_description'),callback_data="book_description")],
            [InlineKeyboardButton(text=t(lang,'btn_upload_library_book'),callback_data=f"upload_library_book:{i}")]
        ]
    )
    await message.answer(
        t(lang, 'book_selected', i=i, creator= book['creator'],title=book['title']),
        reply_markup=kb,
        parse_mode = 'HTML'
    )




# Описание текущей книги из МЕНЮ ЧИТАТЕЛЯ
@router_book.callback_query(F.data == "current_book")
async def description_current_book(callback: CallbackQuery, state: FSMContext, reader: Reader):
    lang = reader.lang_interface
    await callback.answer()
    if not reader:
        await callback.answer(t(lang,'invalid_book'))
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
    await callback.message.delete()



# Описание книги
@router_book.callback_query(F.data == "book_description")
async def book_description(call: CallbackQuery, state: FSMContext):
    message = call.message
    data = await state.get_data()
    book_info = data.get("book_info", {})
    description = strip_html(book_info['description'])

    caption = (
        f"<b>Author</b>: {book_info['creator']}\n"
        f"<b>Book</b>: {book_info['title']}\n"
        f"<b>Total paragraphs</b>: {book_info['total_paragraphs']}"
        f"\n{description}"
    )
    # параллельно перевод
    description_ru = await translator(description)
    if book_info.get('cover_image'):  # если есть байты картинки
        photo = BufferedInputFile(book_info['cover_image'], filename="cover.jpg")
        await message.answer_photo(photo=photo, caption=caption, parse_mode="HTML")

    else:
        await message.answer(caption)

    # Описание на русском
    await message.answer(
        text=f"<tg-spoiler>{description_ru}</tg-spoiler>",
        parse_mode="HTML",
    )
def strip_html(text: str) -> str:
    text = re.sub(r'<[^>]+>', '', text)
    return re.sub(r'\s+', ' ', text).strip()



# Выбрать книгу из библиотек
@router_book.callback_query(F.data.startswith("upload_library_book:"))
async def select_library_book(callback: CallbackQuery, state: FSMContext, reader):
    await callback.answer()
    i = callback.data.split(":")[1]
    data = await state.get_data()
    books_map = data.get("books_map", {})
    file_hash = books_map[i]['hash']
    await set_book(callback.message, file_hash, reader, state)


# Загрузить собственную книгу
@router_book.message(Command("upload"))
async def upload_my_book(message: Message, state: FSMContext, reader):
    await message.answer(t(reader.lang_interface,'upload_book'))
    await state.set_state(UploadBook.waiting_epub)
@router_book.message(UploadBook.waiting_epub)
async def handler_waiting_epub(message: Message, bot: Bot, state: FSMContext, reader):
    lang = reader.lang_interface
    library = Library()
    if not message.document or not message.document.file_name.endswith(".epub"):
        await message.answer(t(lang,'upload_error'),reply_markup=cancel_kb())
        return
    if message.document.file_size > 10 * 1024 * 1024:
        await message.answer(t(lang, 'upload_too_large'), reply_markup=cancel_kb())
        return

    original_name = message.document.file_name
    file = await bot.get_file(message.document.file_id)

    buf = BytesIO()
    await bot.download_file(file.file_path, destination=buf)
    buf.seek(0)
    file_hash = library.calculate_hash_buffer(buf)

    # Проверяем, есть ли книга в библиотеке
    books = DB_library().list_books() # возвращает {hash: {filename, total_paragraphs}}
    if file_hash in books: # 🔎 Если уже есть по хэшу
        await message.answer(t(lang,'exist_book'))
    else:  # 📥 Если новая книга
        final_name = PATH_EN_BOOKS / original_name
        buf.seek(0)
        final_name.write_bytes(buf.read())  # пишем на диск только если нужно
        library.add_book(final_name) # сохраняем книгу в DB

    await set_book(message, file_hash, reader, state)
    await state.set_state(None)


# УСТАНОВКА книги ОКОНЧАТЕЛЬНАЯ функция
async def set_book(message, file_hash, reader, state: FSMContext):
    db = reader.db
    lang = reader.lang_interface
    user_id= reader.user_id
    book_id = db.get_book_by_hash(file_hash)["id"]
    db.set_current_book(user_id, book_id)
    reader = Reader(user_id)
    await message.answer(
        t(lang,'book_set',book_title=reader.book_title),
        parse_mode='HTML'
    )
    await state.set_state(None)




# Изменить Время
@router_book.callback_query(F.data == "change_time")
async def change_time(callback: CallbackQuery, state: FSMContext, reader):
    user_id = reader.user_id
    db = reader.db
    await callback.answer()  # 🔴 обязательно
    time = db.get_time(user_id)
    await callback.message.edit_text(
        t(reader.lang_interface, 'change_time', time=time),
        parse_mode="HTML",
    )
    await state.set_state(StateUser.waiting_time)
@router_book.message(StateUser.waiting_time)
async def save_time(message: Message, state: FSMContext, reader):
    user_id = reader.user_id
    lang = reader.lang_interface
    db = reader.db
    time = message.text.strip()
    try:
        hours, minutes = map(int, time.split(":"))
        if time.count(":") != 1:
            raise ValueError
        elif not (0 <= hours <= 23 and 0 <= minutes <= 59):
            raise ValueError
    except ValueError:
        await message.answer(
            t(lang,'invalid_time'),
            parse_mode="HTML",
            reply_markup=cancel_kb()
        )
        return
    # сохраняем время
    db.save_time(user_id, time)
    await message.answer(
        t(lang,'time_saved',time=time),
         parse_mode = "HTML",
         )
    await state.set_state(None)


# Изменить скорость чтения
@router_book.callback_query(F.data == "reading_speed")
async def change_reading_speed(callback: CallbackQuery, state: FSMContext, reader):
    user_id = reader.user_id
    db = reader.db
    await callback.answer()
    reading_speed = db.get_reading_speed(user_id)
    await callback.message.edit_text(
        t(reader.lang_interface, 'speed_current', speed=reading_speed),
        parse_mode="HTML"
    )
    await state.set_state(StateUser.waiting_reading_speed)
@router_book.message(StateUser.waiting_reading_speed)
async def save_reading_speed(message: Message, state: FSMContext, reader):
    lang = reader.lang_interface
    user_id = reader.user_id
    db = reader.db
    try:
        speed = int(message.text.strip())
        if speed < 50:
            speed = 50
        elif speed > 150:
            speed = 150
    except ValueError:
        await message.answer(
            t(lang,'speed_invalid'),
            reply_markup=cancel_kb()
        )
        return
    db.save_reading_speed(user_id, speed)
    await message.answer(t(lang,'speed_saved',speed=speed))
    await state.clear()


# Выбрать голос
@router_book.callback_query(F.data == "voice")
async def open_voice_menu(callback: CallbackQuery, reader: Reader):
    await callback.answer()
    voices_lang = detect_lang_simple(reader.description)
    lang = reader.lang_interface
    if voices_lang == 'ru':
        await callback.message.edit_text(
            text= t(lang,'voice_select'),
            reply_markup=voice_menu_ru()
        )
    else:
        await callback.message.edit_text(
            text= t(lang,'voice_select'),
            reply_markup=voice_menu_eng()
        )
@router_book.callback_query(F.data.startswith("voice:"))
async def set_voice(callback: CallbackQuery, reader):
    lang = reader.lang_interface
    user_id = reader.user_id
    db = reader.db
    voice = callback.data.split(":", 1)[1]
    db.save_voice(user_id, voice)
    format_voice = format_voice_name(voice)
    await callback.message.edit_text(
        t(lang,'voice_set',voice=format_voice),
        reply_markup=None,
        parse_mode='HTML'
    )
    await callback.answer()



# Читать с другого абзаца
@router_book.callback_query(F.data == 'set_paragraf_index')
async def change_index(callback: CallbackQuery, state: FSMContext, reader: Reader):
    await callback.answer()
    await callback.message.delete()
    await callback.message.answer(t(reader.lang_interface, 'paragraph_input', total=reader.total_paragraphs))
    await state.set_state(UploadBook.waiting_paragraph)
@router_book.message(UploadBook.waiting_paragraph)
async def save_index(message: Message, state: FSMContext, reader: Reader, sender: Sender):
    lang = reader.lang_interface
    user_id = reader.user_id
    db = reader.db
    if not reader:
        await message.answer(t(lang,'no_book'))
        await state.set_state(None)
        return

    if not message.text.isdigit():
        await message.answer(
            t(lang,'paragraph_only_number'),
            reply_markup=cancel_kb()
        )
        return

    index = int(message.text) - 1

    if index < 0 or index > reader.total_paragraphs:
        await message.answer(
            t(lang,'paragraph_range',total=reader.total_paragraphs),
            reply_markup=cancel_kb()
        )
        return

    db.save_i_chunk(user_id, index)

    await message.answer(t(lang,'paragraph_updated'))
    await next_chunk(message, sender, Reader(user_id), state)
    await state.set_state(None)


# Читаем следующий абзац
@router_book.message(Command("next"))
async def next_chunk(message: Message, sender: Sender, reader: Reader, state: FSMContext):
    if not reader.book_title:
        await start_handler(message, reader, state)
        return

    msg = await message.answer("⏳...")
    try:
        await sender.send_chunk(reader)
    finally:
        with suppress(TelegramBadRequest):
            await msg.delete()


# Удалить книгу
@router_book.callback_query(F.data == 'del_book')
async def del_book(callback: CallbackQuery, reader):
    await callback.answer()
    await callback.message.delete()
    await callback.message.answer(
        t(reader.lang_interface, 'delete_confirm'),
        reply_markup=confirm_kb('del_book')
    )


# Язык интерфейса
@router_book.message(Command("language"))
async def select_language(message: Message, reader):
    reply_markup = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🇷🇺 Русский", callback_data="language:ru")],
            [InlineKeyboardButton(text="🇺🇸 English", callback_data="language:en")],
        ]
    )
    await message.answer(
        t(reader.lang_interface, 'select_language'),
        parse_mode='HTML',
        reply_markup=reply_markup,
    )
@router_book.callback_query(F.data.startswith("language:"))
async def waiting_language(call: CallbackQuery, reader):
    db = reader.db
    user_id = reader.user_id
    language = call.data.split(":", 1)[1]
    db.save_language(user_id,language)
    await call.message.edit_text(
        t(language, 'set_language'),
        parse_mode='HTML',
        reply_markup=None,
    )
    await call.answer()
