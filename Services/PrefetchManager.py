import json
from dataclasses import dataclass
from pathlib import Path
from typing import TextIO


@dataclass
class PrefetchEntry:
    last_index: int
    new_index: int
    chunk: str
    caption: str
    translate_chunk: str
    speed: int
    voice: str
    mp3_path: str


class PrefetchManager:

    @classmethod
    def get(cls, user_id: int, speed: int, voice: str, last_index: int) -> PrefetchEntry | None:
        entry = cls._load(user_id)
        if entry is None:
            return None
        if entry.speed == speed and entry.voice == voice and entry.last_index == last_index:
            if Path(entry.mp3_path).exists():
                return entry
        cls._invalidate(user_id)
        Path(entry.mp3_path).unlink(missing_ok=True)
        return None

    @classmethod
    def set(cls, user_id: int, entry: PrefetchEntry):
        with open(cls._json_path(user_id), "w", encoding="utf-8") as f:
            json.dump({
                "last_index": entry.last_index,
                "new_index": entry.new_index,
                "chunk": entry.chunk,
                "caption": entry.caption,
                "translate_chunk": entry.translate_chunk,
                "speed": entry.speed,
                "voice": entry.voice,
                "mp3_path": entry.mp3_path,
            }, f, ensure_ascii=False)


    @classmethod
    def pop(cls, user_id: int) -> PrefetchEntry | None:
        entry = cls._load(user_id)
        cls._invalidate(user_id)
        return entry

    @classmethod
    def _load(cls, user_id: int) -> PrefetchEntry | None:
        path = cls._json_path(user_id)
        if not Path(path).exists():
            return None
        try:
            with open(path, encoding="utf-8") as f:  # ← вот и причина charmap
                return PrefetchEntry(**json.load(f))
        except Exception as e:
            print(f"⚠️ Prefetch: не удалось загрузить user={user_id}: {e}")
            return None

    @classmethod
    def _invalidate(cls, user_id: int):
        Path(cls._json_path(user_id)).unlink(missing_ok=True)

    @staticmethod
    def _json_path(user_id: int) -> str:
        return f"Cache/{user_id}/prefetch.json"

