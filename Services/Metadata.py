from functools import lru_cache
from pathlib import Path
from ebooklib import epub, ITEM_IMAGE
from PIL import Image
from aiogram.types import BufferedInputFile
from io import BytesIO

# class Metadata:
#     cache = {}
#
#     @staticmethod
#     @lru_cache(maxsize=50)
#     def get_cache(cls, book_path):
#         key = str(book_path)
#         book_time = book_path.stat().st_mtime
#         cached = cls.cache.get(key)
#
#         # если нет cache или файл обновился
#         if not cached or cached["book_time"] != book_time:
#             print("🔥 Parsing epub (cache refresh)")
#             metadata = get_epub_metadata(book_path)
#             cover = metadata[3]
#             cls.cache[key] = {
#                 "book_time": book_time,
#                 "book_title": metadata[0],
#                 "book_creator": metadata[1],
#                 "description": metadata[2],
#                 "cover_image": cover,  # один раз
#                 "thumbnail": make_thumbnail(cover) if cover else None,  # один раз
#             }
#         return cls.cache[key]

class Metadata:
    @staticmethod
    @lru_cache(maxsize=50)
    def get_cache(book_path: Path) -> dict:
        metadata = get_epub_metadata(book_path)
        cover = metadata[3]
        return {
            "book_title": metadata[0],
            "book_creator": metadata[1],
            "description": metadata[2],
            "cover_image": cover,
            "thumbnail": make_thumbnail(cover) if cover else None,
        }



# Метаданные книги
def get_epub_metadata(book_path):
    book = epub.read_epub(str(book_path))

    title = book.get_metadata('DC', 'title')
    creator = book.get_metadata('DC', 'creator')
    description = book.get_metadata('DC', 'description')

    book_title = title[0][0] if title else Path(book_path).stem
    book_creator = creator[0][0] if creator else "нет создателя"
    description = description[0][0] if description else "нет описания"
    cover_image = get_cover(book)

    return book_title, book_creator, description, cover_image


# Получаем картинку книги
def get_cover(book):
    # 1️⃣ Пробуем получить id обложки из metadata
    cover_id = None
    metadata = book.get_metadata("OPF", "cover")

    if metadata:
        cover_id = metadata[0][1].get("content")

    # 2️⃣ Если нашли id — получаем файл
    if cover_id:
        item = book.get_item_with_id(cover_id)
        if item:
            return item.get_content()

    # 3️⃣ Если не нашли — перебираем изображения
    for item in book.get_items_of_type(ITEM_IMAGE):
        name = item.get_name().lower()
        if any(word in name for word in ["cover", "oblozh", "front"]):
            return item.get_content()

    # 4️⃣ Последний fallback — первая картинка в книге
    images = list(book.get_items_of_type(ITEM_IMAGE))
    if images:
        return images[0].get_content()

    return None


# Миниатюру из аудио файла для сообщения
def make_thumbnail(image_bytes: bytes) -> BufferedInputFile:
    with Image.open(BytesIO(image_bytes)) as img:
        img = img.convert("RGB")
        img.thumbnail((320, 320))

        output = BytesIO()
        quality = 85
        while True:
            output.seek(0)
            output.truncate()
            img.save(output, format="JPEG", quality=quality, optimize=True)
            if output.tell() <= 200 * 1024 or quality <= 40:
                break
            quality -= 5

        return BufferedInputFile(file=output.getvalue(), filename="thumb.jpg")

