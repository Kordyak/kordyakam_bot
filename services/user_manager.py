import json
from pathlib import Path

class UserManager:

    BASE_PATH = Path("Users")

    @classmethod
    def get_user_folder(cls, user_id):
        path = cls.BASE_PATH / str(user_id)
        path.mkdir(parents=True, exist_ok=True)
        return path

    @classmethod
    def get_book_path(cls, user_id):
        return cls.get_user_folder(user_id) / "book.epub"

    @classmethod
    def get_state_path(cls, user_id):
        return cls.get_user_folder(user_id) / "state.json"

    @classmethod
    def get_config_path(cls, user_id):
        return cls.get_user_folder(user_id) / "config.json"

    @classmethod
    def reset_state(cls, user_id):
        state_path = cls.get_state_path(user_id)
        state_path.unlink(missing_ok=True)

    @classmethod
    def save_time(cls, user_id, time):
        path = cls.get_config_path(user_id)
        path.write_text(json.dumps({"time": time}))

    @classmethod
    def get_time(cls, user_id):
        path = cls.get_config_path(user_id)
        if not path.exists():
            return None
        data = json.loads(path.read_text())
        return data.get("time")

    @classmethod
    def get_all_users(cls) -> list[int]:
        if not cls.BASE_PATH.exists():
            return []

        users = []

        for path in cls.BASE_PATH.iterdir():
            if path.is_dir() and path.name.isdigit():
                users.append(int(path.name))

        return users
