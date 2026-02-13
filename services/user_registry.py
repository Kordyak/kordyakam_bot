import json
from pathlib import Path

class UserRegistry:

    FILE = Path("users.json")

    @classmethod
    def load(cls):
        if not cls.FILE.exists():
            return {}
        return json.loads(cls.FILE.read_text())

    @classmethod
    def save(cls, data):
        cls.FILE.write_text(json.dumps(data))

    @classmethod
    def set_user_time(cls, user_id, time):
        data = cls.load()
        data[str(user_id)] = {"time": time}
        cls.save(data)