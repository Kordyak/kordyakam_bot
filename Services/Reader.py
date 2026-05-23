from pathlib import Path
from Services.Metadata import Metadata
from Services.Converters import detect_lang_simple
from Services.Library import epub_paragraph_generator, BOOK_PATHS
from SQL.DB_library import DB_library
from functools import lru_cache



# Чтец
class Reader:
    book_title = ""
    book_creator = ""
    description = ""
    cover_image = None
    cached_epub = None

    def __init__(self,
                 user_id: int,
                 db: DB_library,
                 language_code: str | None = None
                 ):
        self.user_id = user_id
        self.db = db
        state = self.db.get_user_state(user_id) # Загружаем состояние пользователя
        self.paragraph_indx = state[0] or 0
        self.daily_time = state[1]
        self.book_name = Path(str(state[2]))
        self.total_paragraphs = state[3] or 0
        self.reading_speed = state[4]
        self.username = state[5]
        self.voice = state[6]
        self.lang_interface = state[7]
        self.lang_book = state[8]


        if self.lang_interface is None:
            self.db.save_language(user_id, language_code)
            self.lang_interface = language_code

        if self.lang_book:
            path_file = Path(BOOK_PATHS[self.lang_book] / self.book_name)
            if path_file.exists():
                metadata = Metadata.get_cache(path_file)
                self.book_title = metadata.get("book_title", "")
                self.book_creator = metadata.get("book_creator", "")
                self.description = metadata.get("description", "")
                self.cover_image = metadata.get("cover_image")
                self.thumbnail = metadata.get("thumbnail")

                if self.voice is None:
                    detect_lang = detect_lang_simple(self.description)
                    if detect_lang == 'ru':
                        self.voice = "ru-RU-SvetlanaNeural"
                    else:
                        self.voice = "en-US-BrianNeural"

            self.cached_epub = CachedEpub(path_file, self.paragraph_indx) # Ленивое чтение epub


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
            paragraph = self.cached_epub.get_next_paragraph()

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
        # self.db.save_i_chunk(self.user_id, self.paragraph_indx)

        if buffer:
            return "\n".join(buffer).strip(), self.paragraph_indx
        else:
            return None, self.paragraph_indx





class CachedEpub:
    @staticmethod
    @lru_cache(maxsize=50)  # максимум 200 книг в памяти
    def _load_paragraphs(path_str: str) -> tuple[str, ...]:
        # tuple вместо list — lru_cache требует hashable
        return tuple(epub_paragraph_generator(Path(path_str)))

    def __init__(self, path, saved_index):
        self._paragraphs = self._load_paragraphs(str(path))
        self._index = saved_index

    def get_next_paragraph(self):
        if self._index >= len(self._paragraphs):
            return None
        paragraph = self._paragraphs[self._index]
        self._index += 1
        return paragraph










