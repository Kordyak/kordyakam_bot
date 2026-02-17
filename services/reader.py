import os
from pathlib import Path
import re
import json

from aiogram import Bot
from aiogram.types import FSInputFile

from services.book_cache import BookCache
from services.converter_service import translate_rus_eng, convert_text_audio
from services.user_manager import UserManager


class Reader:

    TELEGRAM_LIMIT = 1000

    def __init__(self, book_path, state_file):

        self.book_path = Path(book_path)
        self.state_file = Path(state_file)

        cache = BookCache.get_cache(book_path)

        self.paragraphs = cache["paragraphs"]
        self.book_title, self.book_author = cache["metadata"]
        self.mtime = cache["mtime"]

        # user progress
        self.index = self.load_state()
        self.index_all = len(self.paragraphs)

    # PROGRESS
    @property
    def progress(self):
        if self.index_all == 0:
            return 0
        return round((self.index / self.index_all) * 100, 1)

    # STATE
    def load_state(self):
        if self.state_file.exists():
            data = json.loads(self.state_file.read_text())
            return data.get("index", 0)
        return 0

    def save_state(self):
        self.state_file.write_text(
            json.dumps({"index": self.index})
        )

    # MAX SPEED CHUNK BUILDER
    def get_next_chunk(self, min_len=300):

        if self.index >= self.index_all:
            return None

        buffer = []
        current_len = 0   # ⭐ ключевой speed upgrade

        while self.index < self.index_all:

            paragraph = self.paragraphs[self.index]

            buffer.append(paragraph)

            current_len += len(paragraph)   # O(1) вместо sum()

            self.index += 1

            if current_len >= min_len:
                break

        self.save_state()

        return "\n".join(buffer).strip()







class Creating_reader:

    cache = {}

    @classmethod
    def get_reader(cls, user_id):

        book_path = UserManager.get_book_path(user_id)
        if not book_path.exists():
            return None
        state_path = UserManager.get_state_path(user_id)
        mtime = book_path.stat().st_mtime
        reader = cls.cache.get(user_id)

        # create or refresh reader
        if not reader or reader.mtime != mtime:
            print("🔥 Creating NEW reader (file changed)")
            reader = Reader(book_path, state_path)
            cls.cache[user_id] = reader

        return reader




class Sender:

    def __init__(self, bot: Bot):
        self.bot = bot

    async def send_daily_text(self, user_id: int):
        reader = Creating_reader.get_reader(user_id)

        chunk = reader.get_next_chunk()

        if not chunk:
            await self.bot.send_message(user_id, "Книга закончилась 📚")
            return

        audio_file: FSInputFile = convert_text_audio(chunk, "", "en")

        await self.bot.send_audio(
            chat_id=user_id,
            audio=audio_file,
            performer="@KordyakBot",
            title=make_title(chunk),
            caption=(
                f"{reader.book_author} — {reader.book_title}\n"
                f"{reader.progress}%\n"
                f"{chunk}"
            ),
            parse_mode="HTML",
        )

        chunk_rus = translate_rus_eng(chunk, "/en_ru")
        await self.bot.send_message(
            chat_id=user_id,
            text=f"<tg-spoiler>{chunk_rus}</tg-spoiler>",
            parse_mode="HTML",
        )



def smart_telegram_split(text, limit):

    result = ""

    # делим на абзацы
    paragraphs = text.split("\n")

    for paragraph in paragraphs:

        # если добавление абзаца не превышает лимит
        if len(result) + len(paragraph) <= limit:
            result += ("\n" if result else "") + paragraph
            continue

        # если абзац слишком длинный — режем по предложениям
        sentences = re.split(r'(?<=[.!?])\s+', paragraph)

        for sentence in sentences:

            if len(result) + len(sentence) <= limit:
                result += (" " if result else "") + sentence
            else:
                return result.strip()

        # если дошли сюда — лимит достигнут
        if len(result) >= limit:
            break

    return result.strip()





# Заголовок из текста
def make_title(text, words=6, max_len=60):
    # убираем переносы строк
    clean = text.replace("\n", " ").strip()
    # берём первые N слов
    title = " ".join(clean.split()[:words])
    # ограничиваем длину
    return title[:max_len]


# # Отправка сообщения
# async def send_daily_text(bot, user_id):
#
#     reader = ReaderService.get_reader(user_id)
#
#     chunk = reader.get_next_chunk()
#
#     if not chunk:
#         await bot.send_message(user_id, "Книга закончилась 📚")
#         return
#
#     audio_file: FSInputFile = convert_text_audio(chunk, "", "en")
#
#     await bot.send_audio(
#         chat_id=user_id,
#         audio=audio_file,
#         performer="@KordyakBot",
#         title=f"{make_title}",
#         caption=f"{reader.book_author}-{reader.book_title}"
#                 f"\n{reader.progress}%"
#                 f"\n{chunk}",
#         parse_mode='HTML'
#     )
#
#     chunk_rus = translate_rus_eng(chunk, "/en_ru")
#     await bot.send_message(chat_id= user_id,
#                             text=f"<tg-spoiler>{chunk_rus}</tg-spoiler>",
#                             parse_mode = 'HTML')
#     os.remove(audio_file.filename)







