import json
from pathlib import Path


class StateUser:

    BASE_PATH = Path("Users")
    _cache: dict[int, dict] = {}

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

    # 🔹 Новый метод: загрузка с кэшем
    @classmethod
    def _get_cached_state(cls, user_id: int) -> dict:
        if user_id in cls._cache:
            return cls._cache[user_id]

        path = cls.get_state_path(user_id)
        if not path.exists():
            cls._cache[user_id] = {}
        else:
            cls._cache[user_id] = json.loads(path.read_text(encoding="utf-8"))

        return cls._cache[user_id]

    # 🔹 Сохранение с обновлением кэша
    @classmethod
    def _save_state(cls, user_id: int, data: dict):
        cls._cache[user_id] = data
        path = cls.get_state_path(user_id)
        path.write_text(
            json.dumps(data, ensure_ascii=False, indent=4),
            encoding="utf-8"
        )

    # 🔹 Опционально: ручной сброс кэша
    @classmethod
    def clear_cache(cls, user_id: int | None = None):
        if user_id is None:
            cls._cache.clear()
        else:
            cls._cache.pop(user_id, None)

    # -----------------------
    # Работа с книгой
    # -----------------------

    @classmethod
    def get_book_path(cls, user_id: int) -> Path | None:
        data = cls._get_cached_state(user_id)
        book_path = data.get("book_path")
        return Path(book_path) if book_path else None

    @classmethod
    def reset_state(cls, user_id: int, book_path: str):
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
        data = cls._get_cached_state(user_id)
        return data.get("index", 0)

    @classmethod
    def save_index(cls, user_id: int, idx: int):
        data = cls._get_cached_state(user_id)
        data["index"] = idx
        cls._save_state(user_id, data)

    # -----------------------
    # Работа со ВРЕМЕНЕМ
    # -----------------------

    @classmethod
    def save_time(cls, user_id: int, time: str):
        data = cls._get_cached_state(user_id)
        data["time"] = time
        cls._save_state(user_id, data)

    @classmethod
    def get_time(cls, user_id: int) -> str | None:
        data = cls._get_cached_state(user_id)
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
