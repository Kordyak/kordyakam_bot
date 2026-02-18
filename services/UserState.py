import json
from pathlib import Path


class UserState:

    BASE_PATH = Path("Users")

    # -----------------------
    # Вспомогательные методы
    # -----------------------

    @classmethod
    def get_user_folder(cls, user_id: int) -> Path:
        path = cls.BASE_PATH / str(user_id)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def get_state_path(cls, user_id: int) -> Path:
        return cls.get_user_folder(user_id) / "state.json"

    @classmethod
    def _load_state(cls, user_id: int) -> dict:
        path = cls.get_state_path(user_id)
        if not path.exists():
            return {}
        return json.loads(path.read_text(encoding="utf-8"))

    @classmethod
    def _save_state(cls, user_id: int, data: dict):
        path = cls.get_state_path(user_id)
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=4),
            encoding="utf-8"
        )

    # -----------------------
    # Работа с книгой
    # -----------------------

    @classmethod
    def get_book_path(cls, user_id: int) -> Path | None:
        data = cls._load_state(user_id)
        book_path = data.get("book_path")
        if not book_path:
            return None
        else:
            return Path(book_path)

    @classmethod
    def set_state(cls, user_id: int, book_path: str):
        cls._save_state(user_id, {
            "index": 0,
            "time": "",
            "book_path": str(book_path)
        })

    # -----------------------
    # Работа со ИНДЕКСОМ
    # -----------------------

    @classmethod
    def get_index(cls, user_id: int) -> int:
        data = cls._load_state(user_id)
        return data.get("index", 0)

    @classmethod
    def save_index(cls, user_id: int, idx: int):
        data = cls._load_state(user_id)
        data["index"] = idx
        cls._save_state(user_id, data)

    # -----------------------
    # Работа со ВРЕМЕНЕМ
    # -----------------------


    @classmethod
    def save_time(cls, user_id: int, time: str):
        data = cls._load_state(user_id)
        data["time"] = time
        cls._save_state(user_id, data)

    @classmethod
    def get_time(cls, user_id: int) -> str | None:
        data = cls._load_state(user_id)
        return data.get("time")

    # -----------------------
    # Пользователи
    # -----------------------

    @classmethod
    def get_all_users(cls) -> list[int]:
        if not cls.BASE_PATH.exists():
            return []

        return [
            int(path.name)
            for path in cls.BASE_PATH.iterdir()
            if path.is_dir() and path.name.isdigit()
        ]

