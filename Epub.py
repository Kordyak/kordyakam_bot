import json
import os
from pathlib import Path

from aiogram.types import FSInputFile
from ebooklib import epub, ITEM_DOCUMENT
from bs4 import BeautifulSoup
from config import chat_id_IA
import re

from services.service_1 import translate_rus_eng, convert_text_audio


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



class ReaderService:

    TELEGRAM_LIMIT = 1000

    def __init__(self, book_path, state_file="reader_state.json"):

        self.book_path = book_path
        self.state_file = Path(state_file)

        # Загружаем все параграфы (или чанки)
        self.paragraphs = list(epub_paragraph_generator(book_path))

        # текущий индекс
        self.index = self.load_state()

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
async def send_daily_text(bot, reader):

    chunk = reader.get_next_chunk()

    if not chunk:
        await bot.send_message(chat_id_IA, "Книга закончилась 📚")
        return

    audio_file: FSInputFile = convert_text_audio(chunk, "", "en")

    await bot.send_audio(
        chat_id=chat_id_IA,
        audio=audio_file,
        performer="kordyak_bot",
        title=make_title(chunk),
        caption=chunk,
        parse_mode='HTML'
    )

    text_rus = translate_rus_eng(chunk, "/en_ru")
    await bot.send_message(chat_id= chat_id_IA,
                            text=f"<tg-spoiler>{text_rus}</tg-spoiler>",
                            parse_mode = 'HTML')
    os.remove(audio_file.filename)







