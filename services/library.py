import json
import hashlib
from pathlib import Path

BOOK_DIR = Path("Book")
BOOK_DIR.mkdir(exist_ok=True)

INDEX_FILE = BOOK_DIR / "books_index.json"


class Library:

    @staticmethod
    def _load_index() -> dict:
        if not INDEX_FILE.exists():
            return {}

        with open(INDEX_FILE, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _save_index(data: dict):
        with open(INDEX_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=4)

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
        index = cls._load_index()
        return file_hash in index

    @classmethod
    def add_book(cls, file_path: Path):
        file_hash = cls.calculate_hash(file_path)
        index = cls._load_index()
        index[file_hash] = file_path.name
        cls._save_index(index)
