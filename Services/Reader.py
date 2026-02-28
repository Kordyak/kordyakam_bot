import os
import re
from pathlib import Path

from aiogram import Bot
from aiogram.types import FSInputFile, BufferedInputFile

from Services.BookMetadata import BookMetadata
from Services.Converters import translate_rus_eng, convert_text_audio
from Services.Library import epub_paragraph_generator, Library, load_books_index
from Services.UserState import UserState

from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB


# КЭШИРОВАНИЕ reader
class ReaderCache:
    cache = {}

    @classmethod
    def get_reader(cls, user_id):
        book_path = UserState.get_book_path(user_id)

        if book_path is None:
            cls.cache.pop(user_id, None)
            return None

        reader = cls.cache.get(user_id)

        # Если нет в кэше — создаём
        if reader is None:
            print("🔥 Creating NEW reader (no cache)")
            reader = Reader(book_path, user_id)
            cls.cache[user_id] = reader
            return reader

        # Если книга изменилась — пересоздаём
        if reader.book_path != book_path:
            print("♻ Book changed — recreating reader")
            reader = Reader(book_path, user_id)
            cls.cache[user_id] = reader
            return reader

        return reader


# Читатель по сути user (разночтения с КЭШ, надо править)
class Reader:
    TELEGRAM_LIMIT = 1000
    start_index = 0

    def __init__(self, book_path, user_id):
        self.book_path = Path(book_path)
        self.user_id = user_id

        book_metadata = BookMetadata.get_cache(book_path)
        self.book_title = book_metadata["book_title"]
        self.book_creator = book_metadata["book_creator"]
        self.description = book_metadata["description"]
        self.cover_image = book_metadata["cover_image"]

        self.index = UserState.get_index(self.user_id)
        self.time = UserState.get_time(self.user_id)

        # Получаем hash книги и суммарный индекс книги
        file_hash = Library.calculate_hash(book_path)
        books_index = load_books_index()
        book_entry = books_index.get(file_hash, {})
        self.index_all = book_entry.get("total_paragraphs", 0)

        self.reader = LazyEpubReader(book_path, self.index)

    # PROGRESS
    @property
    def progress(self):
        if self.index_all == 0:
            return 0
        return round((self.index / self.index_all) * 100, 1)

    # MAX SPEED CHUNK BUILDER
    def get_next_chunk(self, min_len=300):

        self.start_index = self.index+1

        if self.index >= self.index_all:
            return None

        buffer = []
        current_len = 0  # ⭐ ключевой speed upgrade

        # Набираем абзацы
        while self.index < self.index_all:
            paragraph = self.reader.get_next_paragraph()
            if paragraph is None:
                break

            buffer.append(paragraph)
            current_len += len(paragraph)
            self.index += 1

            if current_len >= min_len:
                break

        UserState.save_index(self.user_id, self.index)

        return "\n".join(buffer).strip()


# Ленивое чтение книги, без кэша всей книги
class LazyEpubReader:
    def __init__(self, path, saved_index):
        self.path = path
        self.generator = epub_paragraph_generator(path)
        # Пропускаем уже прочитанные абзацы один раз
        for _ in range(saved_index):
            try:
                next(self.generator)
            except StopIteration:
                break

    def get_next_paragraph(self):
        try:
            paragraph = next(self.generator)
            return paragraph
        except StopIteration:
            return None




# Отправляет ЧАНКИ книги
class Sender:

    def __init__(self, bot: Bot):
        self.bot = bot

    async def send_daily_text(self, user_id: int):
        reader = ReaderCache.get_reader(user_id)

        chunk = reader.get_next_chunk()

        if not chunk:
            await self.bot.send_message(user_id, "Книга закончилась 📚")
            return

        name_file = make_title(chunk)

        convert_text_audio(chunk, name_file, "en")

        # 2. Открываем файл и добавляем теги
        mp3 = MP3(name_file, ID3=ID3)

        if mp3.tags is None:
            mp3.add_tags()

        # Удаляем старую обложку если была
        mp3.tags.delall("APIC")

        # Добавляем обложку
        mp3.tags.add(
            APIC(
                encoding=3,
                mime='image/jpeg',
                type=3,
                desc='Cover',
                data=reader.cover_image  # bytes изображения
            )
        )
        # Удаляем старые ТЭГИ
        mp3.tags.delall("TIT2")
        mp3.tags.delall("TPE1")
        mp3.tags.delall("TALB")
        # Добавим нормальные теги (чтобы Telegram красиво показывал)
        mp3.tags.add(TIT2(encoding=3, text=name_file))
        mp3.tags.add(TPE1(encoding=3, text=reader.book_creator))
        mp3.tags.add(TALB(encoding=3, text=reader.book_title))

        mp3.save()

        await self.bot.send_audio(
            chat_id=user_id,
            audio=FSInputFile(name_file),
            performer=reader.book_title,
            title=name_file,
            caption=(
                f"{reader.book_creator} / <b>{reader.book_title}</b>\n"
                f"Прогресс: <b>{reader.progress} %</b>\n"
                f"Абзац: <b>№№ {reader.start_index} - {reader.index}</b>\n"
                f"{chunk}"
            ),
            parse_mode="HTML",
        )
        os.remove(name_file)

        chunk_rus = translate_rus_eng(chunk, "/en_ru")
        await self.bot.send_message(
            chat_id=user_id,
            text=f"<tg-spoiler>{chunk_rus}</tg-spoiler>",
            parse_mode="HTML",
        )


# Заголовок из текста
def make_title(text, words=6, max_len=60):
    # убираем переносы строк
    clean = re.sub(r'[<>:"/\\|?*]', '', text)
    # берём первые N слов
    title = " ".join(clean.split()[:words])
    # ограничиваем длину
    return title[:max_len]
