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