import json
import sqlite3
from pathlib import Path
from datetime import datetime, timedelta

PATH_READ_DB = Path("SQL/read.db")


class ReadRepository:

    def __init__(self):
        self.db_path = PATH_READ_DB
        self._init_db()

    # CONNECTION
    def _get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.execute("PRAGMA foreign_keys = ON")
        return conn

    # INIT
    def _init_db(self):
        with self._get_connection() as conn:
            conn.executescript("""

            CREATE TABLE IF NOT EXISTS books (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL UNIQUE,
                hash TEXT NOT NULL UNIQUE,
                total_paragraphs INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            );

            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                daily_time TEXT DEFAULT '08:00',

                current_book_id INTEGER,
                chunk_index INTEGER DEFAULT 0 CHECK(chunk_index >= 0),

                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

                FOREIGN KEY (current_book_id) 
                    REFERENCES books(id) 
                    ON DELETE SET NULL
            );

            CREATE INDEX IF NOT EXISTS idx_books_hash ON books(hash);

            """)

    # ============================ USER ============================================
    def get_or_create_user(self, telegram_id: int, username: str | None = None):

        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT user_id FROM users WHERE user_id=?",
                (telegram_id,)
            )
            row = cursor.fetchone()

            if row:
                return telegram_id

            conn.execute("""
                INSERT INTO users (user_id, username)
                VALUES (?, ?)
            """, (telegram_id, username))

            return telegram_id

    def get_i_chunk(self, user_id: int) -> int:
        with self._get_connection() as conn:
            cur = conn.execute("SELECT chunk_index FROM users WHERE user_id = ?", (user_id,))
            row = cur.fetchone()
            return row[0] if row else 0

    def save_i_chunk(self, telegram_id: int, idx: int):
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE users
                SET chunk_index=?
                WHERE user_id=?
            """, (idx, telegram_id))

    def set_current_book(self, telegram_id: int, book_id: int):
        """Назначает пользователю книгу по id, сбрасывает прогресс"""
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE users
                SET current_book_id=?,
                    chunk_index=0
                WHERE user_id=?
            """, (book_id, telegram_id))

    def get_time(self, telegram_id: int) -> str | None:
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT daily_time FROM users WHERE user_id=?", (telegram_id,)
            ).fetchone()
            return row[0] if row else None

    def save_time(self, telegram_id: int, time: str):
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE users
                SET daily_time=?
                WHERE user_id=?
            """, (time, telegram_id))

    def list_users_with_time(self) -> list[dict]:
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT user_id, username, daily_time
                FROM users
                WHERE daily_time IS NOT NULL
            """).fetchall()

        return [
            {
                "user_id": r[0],
                "username": r[1],
                "daily_time": r[2],
            }
            for r in rows
        ]


    def get_users_to_send(self, now: datetime):
        now_str = now.strftime("%H:%M")

        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT user_id, username, daily_time
                FROM users
                WHERE daily_time = ?
            """, (now_str,)).fetchall()
        return [
            {
                "user_id": r[0],
                "username": r[1],
                "daily_time": r[2],
            }
            for r in rows
        ]

    def remove_current_book(self, telegram_id: int):
        """Удаляет текущую книгу у пользователя и сбрасывает прогресс"""
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE users
                SET current_book_id = NULL,
                    chunk_index = 0
                WHERE user_id = ?
            """, (telegram_id,))

    # INCREMENT PROGRESS
    def increment_progress(self, telegram_id: int, step: int = 1) -> tuple[int, bool]:

        with self._get_connection() as conn:

            cursor = conn.execute("""
                SELECT u.chunk_index, b.total_paragraphs
                FROM users u
                JOIN books b ON u.current_book_id = b.id
                WHERE u.user_id = ?
            """, (telegram_id,))

            row = cursor.fetchone()

            if not row:
                return 0, False  # книги нет

            chunk_index, total_paragraphs = row

            new_index = chunk_index + step

            if new_index >= total_paragraphs:
                new_index = total_paragraphs
                is_completed = True
            else:
                is_completed = False

            conn.execute("""
                UPDATE users
                SET chunk_index = ?
                WHERE user_id = ?
            """, (new_index, telegram_id))

            return new_index, is_completed

    # LIBRARY METHODS
    def list_books(self) -> dict[str, dict]:
        """Возвращает список всех книг в библиотеке"""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM books
            """).fetchall()
        # сначала сортируем по filename (r[1])
        rows = sorted(rows, key=lambda r: r[1])

        # затем формируем dict по hash
        return {
            r[2]: {
                "id": r[0],
                "filename": r[1],
                "total_paragraphs": r[3]
            }
            for r in rows
        }

    def add_book(self, filename: str, file_hash: str, total_paragraphs: int) -> int:
        """Добавляет книгу в библиотеку, возвращает её id"""
        with self._get_connection() as conn:
            conn.execute("""
                INSERT OR IGNORE INTO books (filename, hash, total_paragraphs)
                VALUES (?, ?, ?)
            """, (filename, file_hash, total_paragraphs))

            book_id = conn.execute(
                "SELECT id FROM books WHERE hash=?", (file_hash,)
            ).fetchone()[0]
        return book_id

    def get_all_books(self):
        with self._get_connection() as conn:
            return conn.execute("SELECT id, filename FROM books").fetchall()

    def delete_book(self, book_id):
        with self._get_connection() as conn:
            conn.execute("DELETE FROM books WHERE id = ?", (book_id,))

    # Получить книгу по hash
    def get_book_by_hash(self, file_hash: str) -> dict | None:
        """
        Возвращает словарь с информацией о книге:
        {
            'id': int,
            'filename': str,
            'hash': str,
            'total_paragraphs': int
        }
        или None, если книги нет
        """
        query = "SELECT id, filename, hash, total_paragraphs FROM books WHERE hash=?"
        with self._get_connection() as conn:
            cursor = conn.execute(query, (file_hash,))
            row = cursor.fetchone()
            if row:
                return {
                    "id": row[0],
                    "filename": row[1],
                    "hash": row[2],
                    "total_paragraphs": row[3],
                }
        return None

    # GET user STATE
    def get_user_state(self, telegram_id: int):
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    u.chunk_index,
                    u.daily_time,
                    b.filename,
                    b.total_paragraphs
                FROM users u
                LEFT JOIN books b ON u.current_book_id = b.id
                WHERE u.user_id = ?
            """, (telegram_id,))

            return cursor.fetchone()

    # Migration BOOKS
    def migrate_books_index(self, books_index_path: Path):

        if not books_index_path.exists():
            print("books_index.json не найден")
            return

        with open(books_index_path, "r", encoding="utf-8") as f:
            books_data = json.load(f)

        with self._get_connection() as conn:

            for file_hash, data in books_data.items():
                filename = data["filename"]
                total = data["total_paragraphs"]

                conn.execute("""
                    INSERT OR IGNORE INTO books (filename, hash, total_paragraphs)
                    VALUES (?, ?, ?)
                """, (filename, file_hash, total))

        print(f"Миграция books_index.json завершена ✅ ({len(books_data)} книг)")

    # Migration USERS
    def migrate_states(self, users_root: Path):

        if not users_root.exists():
            print("Users папка не найдена")
            return

        with self._get_connection() as conn:

            for user_folder in users_root.iterdir():

                if not user_folder.is_dir():
                    continue

                telegram_id = int(user_folder.name)
                state_file = user_folder / "state.json"

                if not state_file.exists():
                    continue

                with open(state_file, "r", encoding="utf-8") as f:
                    state = json.load(f)

                index = state.get("index", 0)
                daily_time = state.get("time", "08:00")
                book_path = state.get("book_path")

                # создаём пользователя
                conn.execute("""
                    INSERT OR IGNORE INTO users (user_id, daily_time)
                    VALUES (?, ?)
                """, (telegram_id, daily_time))

                if not book_path:
                    continue

                filename = Path(book_path).name

                # получаем книгу
                cursor = conn.execute("""
                    SELECT id FROM books WHERE filename=?
                """, (filename,))

                row = cursor.fetchone()

                if not row:
                    print(f"⚠ Книга {filename} не найдена в books — пропускаем")
                    continue

                book_id = row[0]

                # обновляем пользователя
                conn.execute("""
                    UPDATE users
                    SET current_book_id=?,
                        chunk_index=?
                    WHERE user_id=?
                """, (book_id, index, telegram_id))

        print("Миграция state.json завершена ✅")
