import os
import re
from pathlib import Path
from io import BytesIO

from aiogram import Bot
from aiogram.types import FSInputFile, BufferedInputFile

from Services.BookMetadata import BookMetadata
from Services.Converters import translate_rus_eng, convert_text_audio
from SQL.RR import ReadRepository

from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB
from PIL import Image
from Services.Library import PATH_BOOKS, epub_paragraph_generator


class Reader:
    TELEGRAM_LIMIT = 1000
    book_title = None
    book_creator = None
    description = None
    cover_image = None

    def __init__(self, user_id: int, username: str | None = None):
        self.user_id = user_id
        self.rr = ReadRepository()

        # Создаём пользователя, если нет
        self.rr.get_or_create_user(user_id, username)

        # Загружаем состояние пользователя
        state = self.rr.get_user_state(user_id)

        self.index = state[0] or 0  # chunk_index
        self.daily_time = state[1]
        self.book_name = Path(str(state[2]))
        self.total_paragraphs = state[3] or 0  # total_paragraphs

        path_file = Path(PATH_BOOKS / self.book_name)

        if path_file.exists():
            metadata = BookMetadata.get_cache(path_file)
            self.book_title = metadata.get("book_title", "")
            self.book_creator = metadata.get("book_creator", "")
            self.description = metadata.get("description", "")
            self.cover_image = metadata.get("cover_image")

            # Ленивое чтение epub
            self.lazy_read = LazyEpubReader(path_file, self.index)

    @property
    def progress(self):
        if self.total_paragraphs == 0:
            return 0
        return round((self.index / self.total_paragraphs) * 100, 1)

    def get_next_chunk(self, min_len=300):
        if self.index >= self.total_paragraphs:
            return None

        buffer = []
        current_len = 0

        while self.index < self.total_paragraphs:
            paragraph = self.lazy_read.get_next_paragraph()

            if paragraph is None:
                break
            buffer.append(paragraph)
            current_len += len(paragraph)
            self.index += 1
            if current_len >= min_len:
                break

        # Сохраняем прогресс
        self.rr.save_i_chunk(self.user_id, self.index)

        return "\n".join(buffer).strip()



# -----------------------
# Ленивое чтение epub
# -----------------------


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





# -----------------------
# Отправка чанк текста пользователю
# -----------------------
class Sender:
    def __init__(self, bot: Bot):
        self.bot = bot

    async def send_daily_text(self, user_id: int):
        reader = Reader(user_id)
        chunk = reader.get_next_chunk()

        if not chunk:
            await self.bot.send_message(user_id, "Книга закончилась 📚")
            return

        name_file = make_title(chunk)
        convert_text_audio(chunk, name_file, "en")
        rewrite_mp3_tags(name_file, reader)
        thumbnail = make_thumbnail(reader.cover_image)

        await self.bot.send_audio(
            chat_id=user_id,
            audio=FSInputFile(name_file),
            thumbnail=thumbnail,
            performer=reader.book_title,
            title=name_file,
            caption=(
                f"{reader.book_creator} / <b>{reader.book_title}</b>\n"
                f"Прогресс: <b>{reader.progress} %</b>\n"
                f"Абзац: <b>№№ {reader.index - len(chunk.splitlines()) + 1} - {reader.index}</b>\n"
                f"{chunk}"
            ),
            parse_mode="HTML",
        )
        os.remove(name_file)

        # Перевод
        chunk_rus = translate_rus_eng(chunk, "/en_ru")
        await self.bot.send_message(
            chat_id=user_id,
            text=f"<tg-spoiler>{chunk_rus}</tg-spoiler>",
            parse_mode="HTML",
        )


# -----------------------
# Миниатюра в mp3 файле
# -----------------------
def rewrite_mp3_tags(file_path: str, reader: Reader):
    try:
        ID3(file_path).delete(file_path)
    except Exception:
        pass

    tags = ID3()
    tags.add(APIC(encoding=3, mime="image/jpeg", type=3, desc="Cover", data=reader.cover_image))
    tags.add(TIT2(encoding=3, text=reader.book_title))
    tags.add(TPE1(encoding=3, text=reader.book_creator))
    tags.add(TALB(encoding=3, text=reader.book_title))
    tags.save(file_path, v2_version=3)
    MP3(file_path)


def make_thumbnail(image_bytes: bytes) -> BufferedInputFile:
    with Image.open(BytesIO(image_bytes)) as img:
        img = img.convert("RGB")
        img.thumbnail((320, 320))

        output = BytesIO()
        quality = 85
        while True:
            output.seek(0)
            output.truncate()
            img.save(output, format="JPEG", quality=quality, optimize=True)
            if output.tell() <= 200 * 1024 or quality <= 40:
                break
            quality -= 5

        return BufferedInputFile(file=output.getvalue(), filename="thumb.jpg")


def make_title(text, words=6, max_len=60):
    clean = re.sub(r'[<>:"/\\|?*]', '', text)
    title = " ".join(clean.split()[:words])
    return title[:max_len]
