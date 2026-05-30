import json
import sqlite3
from pathlib import Path
from datetime import datetime

PATH_READ_DB = Path("SQL/read.db")


class DB_library:

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
                filename TEXT NOT NULL,
                hash TEXT NOT NULL UNIQUE,
                total_paragraphs INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                book_lang TEXT
            );

            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                daily_time TEXT DEFAULT '08:00',
                current_book_id INTEGER,
                chunk_index INTEGER DEFAULT 0 CHECK(chunk_index >= 0),
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                reading_speed INTEGER DEFAULT 88,
                last_access TIMESTAMP,
                voice TEXT,
                language TEXT,
                FOREIGN KEY (current_book_id)
                    REFERENCES books(id)
                    ON DELETE SET NULL
            );

            CREATE INDEX IF NOT EXISTS idx_books_hash ON books(hash);
            """
)


    # ============================ USER ============================================
    def get_create_user(self, telegram_id: int, username: str | None = None):
        with self._get_connection() as conn:
            cursor = conn.execute(
                "SELECT username FROM users WHERE user_id=?",
                (telegram_id,)
            )
            row = cursor.fetchone()
            date = datetime.now().strftime("%d.%m.%Y %H:%M")
            if row:
                conn.execute(
                    """
                        UPDATE users
                        SET last_access=?, username=?
                        WHERE user_id=?
                    """,(date, username, telegram_id)
                )
            else:
                conn.execute(
                    """
                    INSERT INTO users (last_access, username, user_id)
                    VALUES (?, ?, ?)
                    """,(date, username, telegram_id)
                )


    def save_i_chunk(self, telegram_id: int, idx: int):
        with self._get_connection() as conn:
            conn.execute(
                """
                UPDATE users
                SET chunk_index=?
                WHERE user_id=?
            """, (idx, telegram_id)
            )

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
        with self._get_connection() as connection:
            row = connection.execute(
                "SELECT daily_time FROM users WHERE user_id=?",
                (telegram_id,)
            ).fetchone()
            return row[0] if row else None

    def save_time(self, telegram_id: int, time: str):
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE users
                SET daily_time=?
                WHERE user_id=?
            """, (time, telegram_id))

    def remove_daily_time(self, telegram_id: int):
        """Удаляет текущую книгу у пользователя и сбрасывает прогресс"""
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE users
                SET daily_time = NULL
                WHERE user_id = ?
            """, (telegram_id,))

    def get_reading_speed(self, telegram_id: int) -> str | None:
        with self._get_connection() as conn:
            row = conn.execute(
                "SELECT reading_speed FROM users WHERE user_id=?",
                (telegram_id,)
            ).fetchone()
            return row[0] if row else None

    def save_reading_speed(self, telegram_id: int, speed: int):
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE users
                SET reading_speed=?
                WHERE user_id=?
            """, (speed, telegram_id))

    def save_voice(self, user_id:int, voice:str):
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE users
                SET voice=?
                WHERE user_id=?
            """, (voice, user_id))

    def save_language(self, user_id:int, language:str):
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE users
                SET language=?
                WHERE user_id=?
            """, (language, user_id))



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

    def get_users_by_time(self, now: datetime):
        now_str = now.strftime("%H:%M")

        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT user_id, username, daily_time, current_book_id
                FROM users
                WHERE daily_time = ? AND current_book_id IS NOT NULL
            """, (now_str,)).fetchall()
        return [
            {
                "user_id": r[0],
                "username": r[1],
                "daily_time": r[2],
                "current_book_id": r[3],
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

    # GET user STATE
    def get_user_info(self, telegram_id: int):
        with self._get_connection() as conn:
            cursor = conn.execute("""
                SELECT 
                    u.chunk_index,
                    u.daily_time,
                    b.filename,
                    b.total_paragraphs,
                    u.reading_speed,
                    u.username,
                    u.voice,
                    u.language,
                    b.book_lang
                FROM users u
                LEFT JOIN books b ON u.current_book_id = b.id
                WHERE u.user_id = ?
            """, (telegram_id,))

            return cursor.fetchone()

    # ======================== BOOK =======================================
    def list_books(self, book_lang:str) -> dict[str, dict]:
        """Возвращает список всех книг в библиотеке"""
        with self._get_connection() as conn:
            rows = conn.execute("""
                SELECT * FROM books
                WHERE book_lang = ?
            """, (book_lang,)).fetchall()

        # затем формируем dict по hash
        return {
            r[2]: {
                "id": r[0],
                "filename": r[1],
                "total_paragraphs": r[3]
            }
            for r in rows
        }

    def add_book(self, filename: str, file_hash: str, total_paragraphs: int, book_lang: str) -> int:
        """Добавляет книгу в библиотеку, возвращает её id"""
        with self._get_connection() as conn:
            conn.execute("""
                    INSERT OR IGNORE INTO books (filename, hash, total_paragraphs, book_lang)
                    VALUES (?, ?, ?, ?)
                """, (filename, file_hash, total_paragraphs, book_lang))

            book_id = conn.execute(
                "SELECT id FROM books WHERE hash=?", (file_hash,)
            ).fetchone()[0]
        return book_id

    def get_all_books(self):
        with self._get_connection() as conn:
            return conn.execute("SELECT id, filename, book_lang FROM books").fetchall()


    def save_book_lang(self, book_id:int, book_lang:str):
        with self._get_connection() as conn:
            conn.execute("""
                UPDATE books
                SET book_lang=?
                WHERE id=?
            """, (book_lang, book_id))

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

    # ============================== SERVICE ============================

    def get_users_progress(self):
        query = """
        SELECT 
            u.user_id,
            u.username,
            b.filename,
            u.chunk_index,
            b.total_paragraphs,
            ROUND(
                CASE 
                    WHEN b.total_paragraphs > 0 
                    THEN u.chunk_index * 100.0 / b.total_paragraphs
                    ELSE 0
                END, 2
            ) AS progress_percent,
            u.last_access
        FROM users u
        LEFT JOIN books b ON b.id = u.current_book_id
        ORDER BY u.last_access DESC
        """

        with self._get_connection() as conn:
            return conn.execute(query).fetchall()



    def migrate_states(self):
        pass
