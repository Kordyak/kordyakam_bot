import hashlib
from pathlib import Path
import zipfile

from bs4 import BeautifulSoup
from ebooklib import epub, ITEM_DOCUMENT

from SQL.RR_sql import ReadRepository

PATH_BOOKS = Path("Books")


class Library:
    def __init__(self):
        self.db = ReadRepository()

    @staticmethod
    def calculate_hash(path: Path) -> str:
        sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def add_book(self, book_path: Path):
        """
        Добавляет книгу в библиотеку, если её там ещё нет.
        """
        file_hash = self.calculate_hash(book_path)
        existing = self.db.get_book_by_hash(file_hash)
        if existing:
            return file_hash  # Уже есть

        # Считаем количество абзацев
        total_paragraphs = sum(1 for _ in epub_paragraph_generator(book_path))

        # Добавляем в базу
        self.db.add_book(str(book_path.name), file_hash, total_paragraphs)
        return file_hash

    def sync_library(self):
        """
        Проверяет папку Books и синхронизирует её с SQL.
        """

        # 1. Удаляем из базы книги, файлы которых отсутствуют
        books = self.db.get_all_books()  # [(id, filename, hash, ...)]

        for book in books:
            filename = book[1]
            book_path = PATH_BOOKS / filename

            if not book_path.exists():
                print(f"⚠ Файл {filename} отсутствует — удаляем из базы")
                self.db.delete_book(book[0])  # удаление по id

        # 2. Добавляем новые книги
        for book_path in PATH_BOOKS.glob("*.epub"):

            if not zipfile.is_zipfile(book_path):
                print(f"⚠ Файл {book_path.name} поврежден или не EPUB — удаляем")
                book_path.unlink(missing_ok=True)
                continue

            file_hash = self.calculate_hash(book_path)

            if not self.db.get_book_by_hash(file_hash):
                print(f"Добавляю книгу в базу: {book_path.name}")

                total_paragraphs = sum(1 for _ in epub_paragraph_generator(book_path))

                self.db.add_book(str(book_path.name), file_hash, total_paragraphs)



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
