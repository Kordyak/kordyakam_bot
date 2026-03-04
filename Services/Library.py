import hashlib
from pathlib import Path
import zipfile

from SQL.RR import ReadRepository
from Services.Reader import epub_paragraph_generator

BOOK_DIR = Path("Books")
BOOK_DIR.mkdir(exist_ok=True)


class Library:
    def __init__(self, db_path: Path):
        self.db = ReadRepository(db_path)

    @staticmethod
    def calculate_hash(path: Path) -> str:
        sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    def list_books(self) -> dict[str, dict]:
        """
        Возвращает словарь: {hash: {filename, total_paragraphs}}
        """
        books = self.db.list_books()
        return {b["hash"]: {"filename": b["filename"], "total_paragraphs": b["total_paragraphs"]} for b in books}

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
        self.db.insert_book(str(book_path.name), str(book_path), file_hash, total_paragraphs)
        return file_hash

    def sync_library(self):
        """
        Проверяет папку Books и добавляет отсутствующие книги в SQL.
        """
        for book_path in BOOK_DIR.glob("*.epub"):

            if not zipfile.is_zipfile(book_path):
                print(f"⚠ Файл {book_path.name} поврежден или не EPUB — удаляем")
                book_path.unlink(missing_ok=True)
                continue

            file_hash = self.calculate_hash(book_path)

            if not self.db.get_book_by_hash(file_hash):

                print(f"Добавляю книгу в базу: {book_path.name}")

                total_paragraphs = sum(1 for _ in epub_paragraph_generator(book_path))

                self.db.add_book(str(book_path.name), file_hash, total_paragraphs)




