import json
import os
from pathlib import Path

from aiogram.types import FSInputFile
from ebooklib import epub, ITEM_DOCUMENT
from bs4 import BeautifulSoup
from config import chat_id_IA
import re

from services.converter_service import translate_rus_eng, convert_text_audio


def epub_paragraph_generator(epub_path):

    book = epub.read_epub(str(epub_path))

    for item in book.get_items_of_type(ITEM_DOCUMENT):

        soup = BeautifulSoup(item.get_content(), "html.parser")

        for p in soup.find_all("p"):
            text = p.get_text(strip=True)
            if text:
                yield text



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




def get_epub_metadata(book_path):

    book = epub.read_epub(str(book_path))

    title = book.get_metadata('DC', 'title')
    creator = book.get_metadata('DC', 'creator')

    title = title[0][0] if title else Path(book_path).stem
    creator = creator[0][0] if creator else ""

    return title, creator


class Current_book:

    TELEGRAM_LIMIT = 1000

    def __init__(self, book_path, state_file):
        self.book_title, self.book_author = get_epub_metadata(book_path)
        self.book_path = book_path
        self.state_file = Path(state_file)
        # Загружаем все параграфы
        self.paragraphs = list(epub_paragraph_generator(book_path))
        # текущий индекс
        self.index = self.load_state()
        self.index_all = len(self.paragraphs)


    @property
    def progress(self):
        if self.index_all == 0:
            return 0
        return round((self.index / self.index_all) * 100, 1)

    # =====================
    # STATE
    # =====================

    def load_state(self):
        if self.state_file.exists():
            data = json.loads(self.state_file.read_text())
            return data.get("index", 0)
        return 0

    def save_state(self):
        self.state_file.write_text(json.dumps({"index": self.index}))

    # =====================
    # GET NEXT CHUNK
    # =====================

    def get_next_chunk(self, min_len=300):

        if self.index >= len(self.paragraphs):
            return None

        buffer = ""

        # собираем параграфы пока не наберём минимум
        while self.index < len(self.paragraphs):

            paragraph = self.paragraphs[self.index]

            buffer += ("\n" if buffer else "") + paragraph
            self.index += 1

            if len(buffer) >= min_len:
                break

        self.save_state()

        # режем только если превышен telegram limit
        return smart_telegram_split(buffer.strip(), self.TELEGRAM_LIMIT)




# Заголовок из текста
def make_title(text, words=6, max_len=60):
    # убираем переносы строк
    clean = text.replace("\n", " ").strip()
    # берём первые N слов
    title = " ".join(clean.split()[:words])
    # ограничиваем длину
    return title[:max_len]


# Отправка сообщения
async def send_daily_text(bot, current_book):

    chunk = current_book.get_next_chunk()

    if not chunk:
        await bot.send_message(chat_id_IA, "Книга закончилась 📚")
        return

    audio_file: FSInputFile = convert_text_audio(chunk, "", "en")

    await bot.send_audio(
        chat_id=chat_id_IA,
        audio=audio_file,
        performer="@KordyakBot",
        title=f"{current_book.book_author}-{current_book.book_title}-{current_book.progress}%",
        caption=f"{chunk}",
        parse_mode='HTML'
    )

    chunk_rus = translate_rus_eng(chunk, "/en_ru")
    await bot.send_message(chat_id= chat_id_IA,
                            text=f"<tg-spoiler>{chunk_rus}</tg-spoiler>",
                            parse_mode = 'HTML')
    os.remove(audio_file.filename)







