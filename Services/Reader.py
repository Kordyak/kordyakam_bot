from pathlib import Path

from Services.BookMetadata import BookMetadata

from Services.Converters import detect_lang_simple
from Services.Library import PATH_EN_BOOKS, epub_paragraph_generator
from SQL.DB_library import DB_library


# Чтец
class Reader:
    TELEGRAM_LIMIT = 1000
    book_title = None
    book_creator = None
    description = None
    cover_image = None

    def __init__(self,
                 user_id: int,
                 username: str | None = None,
                 lang: str | None = None
                 ):

        self.user_id = user_id

        self.db = DB_library()
        self.db.get_create_user(user_id, username)
        self.db.save_last_contact(user_id)

        state = self.db.get_user_state(user_id) # Загружаем состояние пользователя

        self.paragraph_indx = state[0] or 0
        self.daily_time = state[1]
        self.book_name = Path(str(state[2]))
        self.total_paragraphs = state[3] or 0
        self.reading_speed = state[4]
        self.username = state[5]
        self.voice = state[6]
        self.language = state[7]

        if self.voice is None:
            detect_lang = detect_lang_simple(self.description)
            if detect_lang == 'ru':
                self.voice = "ru-RU-SvetlanaNeural"
            else:
                self.voice = "en-US-BrianNeural"

        if self.language is None:
            self.db.save_language(user_id, lang)
            self.language = lang

        path_file = Path(PATH_EN_BOOKS / self.book_name)
        if path_file.exists():
            metadata = BookMetadata.get_cache(path_file)
            self.book_title = metadata.get("book_title", "")
            self.book_creator = metadata.get("book_creator", "")
            self.description = metadata.get("description", "")
            self.cover_image = metadata.get("cover_image")

            # Ленивое чтение epub
            self.lazy_read = LazyEpubReader(path_file, self.paragraph_indx)




    @property
    def progress(self):
        if self.total_paragraphs == 0:
            return 0
        return round((self.paragraph_indx / self.total_paragraphs) * 100, 1)

    def get_next_chunk(self, min_len=300, max_len=900):
        if self.paragraph_indx >= self.total_paragraphs:
            return None

        buffer = []
        current_len = 0

        while self.paragraph_indx < self.total_paragraphs:
            paragraph = self.lazy_read.get_next_paragraph()

            if paragraph is None:
                break

            paragraph_len = len(paragraph)

            # Проверяем лимит ДО добавления
            if current_len + paragraph_len >= max_len:
                if not buffer:
                    buffer.append(paragraph)
                    self.paragraph_indx += 1
                break

            buffer.append(paragraph)
            current_len += paragraph_len
            self.paragraph_indx += 1

            if current_len >= min_len:
                break

        # Сохраняем прогресс
        self.db.save_i_chunk(self.user_id, self.paragraph_indx)

        return "\n".join(buffer).strip()


# Ленивое чтение epub
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








