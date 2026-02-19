import json
import hashlib
from pathlib import Path

from bs4 import BeautifulSoup
from ebooklib import epub, ITEM_DOCUMENT

BOOK_DIR = Path("Books")
BOOK_DIR.mkdir(exist_ok=True)

INDEX_FILE = BOOK_DIR / "books_index.json"


def load_books_index() -> dict:
    if not INDEX_FILE.exists():
        return {}

    with open(INDEX_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def save_books_index(data: dict):
    with open(INDEX_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=4)


class Library:

    @staticmethod
    def calculate_hash(path: Path) -> str:
        sha256 = hashlib.sha256()
        with open(path, "rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                sha256.update(chunk)
        return sha256.hexdigest()

    @classmethod
    def is_duplicate(cls, file_path: Path) -> bool:
        file_hash = cls.calculate_hash(file_path)
        index = load_books_index()
        return file_hash in index

    @classmethod
    def add_book(cls, book_path: Path):
        file_hash = cls.calculate_hash(book_path)
        index = load_books_index()
        if file_hash not in index:
            # Считаем количество абзацев один раз
            total_paragraphs = sum(1 for _ in epub_paragraph_generator(book_path))
            index[file_hash] = {
                "filename": book_path.name,
                "total_paragraphs": total_paragraphs,
            }
            save_books_index(index)
        return file_hash

    # 🔥 НОВЫЙ МЕТОД
    @classmethod
    def sync_library(cls):
        """
        Проверяет папку Books и добавляет отсутствующие книги в индекс.
        """
        index = load_books_index()
        updated = False

        for book_path in BOOK_DIR.glob("*.epub"):
            file_hash = cls.calculate_hash(book_path)

            if file_hash not in index:
                print(f"Добавляю книгу в индекс: {book_path.name}")

                total_paragraphs = sum(
                    1 for _ in epub_paragraph_generator(book_path)
                )

                index[file_hash] = {
                    "filename": book_path.name,
                    "total_paragraphs": total_paragraphs,
                }

                updated = True

        if updated:
            save_books_index(index)



# Получаем все параграфы книги в массиве
def epub_paragraph_generator(epub_path):
    book = epub.read_epub(str(epub_path))
    for item in book.get_items_of_type(ITEM_DOCUMENT):
        soup = BeautifulSoup(item.get_content(), "html.parser")
        for p in soup.find_all("p"):
            text = p.get_text(strip=True)
            if text:
                yield text

