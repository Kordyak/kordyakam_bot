import hashlib
from io import BytesIO
from pathlib import Path
import zipfile
from bs4 import BeautifulSoup
from ebooklib import epub, ITEM_DOCUMENT
from SQL.DB_library import DB_library

PATH_EN_BOOKS = Path("Books_en")
PATH_RU_BOOKS = Path("Books_ru")

BOOK_PATHS = {
    "en": PATH_EN_BOOKS,
    "ru": PATH_RU_BOOKS,
}


class Library:
    def __init__(self):
        self.db = DB_library()
    # ХЭШ
    @staticmethod
    def calculate_hash(path: Path) -> str:
        sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    @staticmethod
    def calculate_hash_buffer(buffer: BytesIO) -> str:
        sha256 = hashlib.sha256()
        while chunk := buffer.read(8192):
            sha256.update(chunk)
        return sha256.hexdigest()

    # Добавляет книгу в библиотеку, если её там ещё нет.
    def add_book(self, book_path: Path, lang):
        file_hash = self.calculate_hash(book_path)

        if not self.db.get_book_by_hash(file_hash):
            print(f"Добавляю книгу в базу: {book_path.name}")
            try:
                total_paragraphs = sum(1 for _ in epub_paragraph_generator(book_path))
            except Exception as e:
                print(f"Ошибка чтения {book_path.name}: {e}")
                return
            self.db.add_book(str(book_path.name), file_hash, total_paragraphs, lang)

    # Проверяет папку Books и синхронизирует её с SQL.
    def sync_library(self):
        books = self.db.get_all_books()  # теперь возвращает (id, filename, lang)

        for book in books:
            book_id, filename, book_lang = book[0], book[1], book[2]
            book_path = BOOK_PATHS.get(book_lang, PATH_EN_BOOKS) / filename
            if not book_path.exists():
                print(f"⚠ Файл {filename} отсутствует — удаляем из базы")
                self.db.delete_book(book_id)

        # Добавляем новые книги
        for lang, BOOK_PATH in BOOK_PATHS.items():
            for pattern in ("*.epub", "*.fb2"):
                for book_path in BOOK_PATH.glob(pattern):
                    if not zipfile.is_zipfile(book_path):
                        print(f"⚠ Файл {book_path.name} поврежден или не EPUB — удаляем")
                        book_path.unlink(missing_ok=True)
                        continue
                    self.add_book(book_path, lang)




# Получаем все параграфы книги в массиве
def epub_paragraph_generator(epub_path):
    try:
        book = epub.read_epub(str(epub_path))
    except Exception as e:
        print(f"Ошибка чтения EPUB {epub_path.name}: {e}")
        return  # просто пропускаем файл

    for item in book.get_items_of_type(ITEM_DOCUMENT):
        soup = BeautifulSoup(item.get_content(), "html.parser")
        for p in soup.find_all("p"):
            text = p.get_text(strip=True)
            if text:
                yield text
