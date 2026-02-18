import re
from pathlib import Path

from aiogram import Router, F, Bot
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery, BufferedInputFile
from aiogram.filters import Command
from sqlalchemy.util import await_only

from fsm.states import UploadBook
from services.library import Library, BOOK_DIR

from services.reader import Cache_reader, Sender
from services.scheduler_service import SchedulerService

from services.UserState import UserState

book_router = Router(name='book')


def main_menu(reader):
    if not reader:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text="📚 Загрузить книгу", callback_data="upload_book")],
            [InlineKeyboardButton(text="📚 Библиотека книг", callback_data="library")],
        ])


    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text=f"📖У вас есть загруженная книга, информация о ней", callback_data="current_book")],
        [InlineKeyboardButton(text=f"📖Установить номер абзаца с которого начать читать", callback_data="set_paragraf_index")],
        [InlineKeyboardButton(text="🔄 Заменить книгу", callback_data="upload_book")],
        [InlineKeyboardButton(text="▶ Отправь мне очередной абзац", callback_data="next_chunk")],
        [InlineKeyboardButton(text="⏰ Установить время отправки абзаца", callback_data="change_time")],
        [InlineKeyboardButton(text="Удалить подписку на книгу", callback_data="del_subscription")],
    ])


@book_router.message(Command('book'))
async def start(message: Message):
    reader = Cache_reader.get_reader(message.from_user.id)


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

    user_id = message.from_user.id
    if not message.document.file_name.endswith(".epub"):
        await message.answer("Это не epub 😅")
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
    index = Library._load_index()

    # 🔎 Если уже есть по хэшу
    if file_hash in index:
        existing_name = index[file_hash]
        final_path = BOOK_DIR / existing_name

        temp_path.unlink()

        await message.answer("Такая книга уже есть в моей базе 📚")

    # 📥 Если новая книга
    else:
        final_path = BOOK_DIR / original_name
        counter = 1

        while final_path.exists():
            final_path = BOOK_DIR / f"{Path(original_name).stem}_{counter}.epub"
            counter += 1

        temp_path.rename(final_path)

        # сохраняем хэш
        index[file_hash] = final_path.name
        Library._save_index(index)


    # Создаем состояния user
    UserState.set_state(user_id, final_path)
    # Сбрасываем кэш reader если есть
    #Creating_reader.cache.pop(user_id, None)

    Cache_reader.cache.pop(user_id, None)
    reader = Cache_reader.get_reader(user_id)
    await message.answer("Книга загружена 😈",reply_markup=main_menu(reader))


# Задаем Время
@book_router.callback_query(F.data == "change_time")
async def change_time(callback: CallbackQuery):
    await callback.answer()  # 🔴 обязательно
    await callback.message.delete()

    current_time = UserState.get_time(callback.from_user.id)
    time_text = current_time if current_time else "не задано"

    await callback.message.answer(
        f"⏰ Время отправки абзаца.\n"
        f"Сейчас время: <b>{time_text}</b>.\n"
        f"Установить / изменить время?",
        parse_mode="HTML",
        reply_markup=confirm_kb('change_time')
    )



# Задаем Время
@book_router.message(UploadBook.waiting_time)
async def save_time(message: Message, state: FSMContext, sender: Sender):
    time_text = message.text.strip()

    if not re.match(r"^\d{2}:\d{2}$", time_text):
        await message.answer("Формат времени HH:MM 😈")
        return

    user_id = message.from_user.id

    # сохраняем время
    UserState.save_time(user_id, time_text)

    # 🔥 обновляем scheduler
    sender_service = sender
    SchedulerService.create_user_job(sender_service, user_id, time_text)
    Cache_reader.cache.pop(user_id, None)
    reader = Cache_reader.get_reader(user_id)
    await message.answer(f"Время: {time_text} установлено, планировщик включен ✅",
                         reply_markup=main_menu(reader))
    await state.clear()


# Информация о текущей книги
@book_router.callback_query(F.data == "current_book")
async def show_book(callback: CallbackQuery):
    await callback.answer()
    await callback.message.delete()

    id = callback.from_user.id
    reader = Cache_reader.get_reader(id)
    if not reader:
        await  callback.message.answer("Сначала загрузите книгу 📚")
        return

    caption = (
        f"Автор: {reader.book_author}\n"
        f"Книга: {reader.book_title}\n"
        f"Прогресс вашего чтения: {reader.progress}%\n"
        f"Номер последнего отправленного абзаца: №{reader.index}\n"
        f"Время отправки абзаца: {UserState.get_time(id)}\n"
        f"\nОписание книги:\n{reader.description}"
    )

    if reader.cover:  # если есть байты картинки
        photo = BufferedInputFile(reader.cover, filename="cover.jpg")
        await callback.message.answer_photo(photo=photo,caption=caption,reply_markup=main_menu(reader))
    else:
        await callback.message.answer(caption,reply_markup=main_menu(reader))


# Отправить ЧАНК
@book_router.callback_query(F.data == "next_chunk")
async def next_chunk_handler(callback: CallbackQuery, sender: Sender):
    await callback.answer()
    #await callback.message.delete()
    temp_msg = await callback.message.answer('Готовим абзац книги!')
    await sender.send_daily_text(callback.from_user.id)
    await temp_msg.delete()



# установить номер абзаца
@book_router.callback_query(F.data == 'set_paragraf_index')
async def change_index(callback: CallbackQuery, state: FSMContext):
    await callback.answer()
    await callback.message.delete()
    await callback.message.answer('Укажите номер абзаца с которого будем читать')
    await state.set_state(UploadBook.waiting_index)

# установить номер абзаца
@book_router.message(UploadBook.waiting_index)
async def save_index(message: Message, state: FSMContext):
    user_id = message.from_user.id
    reader = Cache_reader.get_reader(user_id)

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

    reader.save_state(index)

    Cache_reader.cache.pop(user_id, None)
    reader = Cache_reader.get_reader(user_id)

    await message.answer("✅ Индекс обновлён!",reply_markup=main_menu(reader))
    await state.clear()



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
        UserState.delete_book(callback.from_user.id)
        await callback.message.edit_text("📚 Книга удалена")


@book_router.callback_query(F.data.startswith("cancel:"))
async def handle_cancel(callback: CallbackQuery):
    await callback.answer()

    action = callback.data.split(":")[1]

    if action == "change_time":
        reader = Cache_reader.get_reader(callback.from_user.id)
        await callback.message.edit_text(
            "👌 Всё оставляем без изменений",
            reply_markup=main_menu(reader)
        )
