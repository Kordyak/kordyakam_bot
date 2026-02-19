from pathlib import Path
from ebooklib import epub, ITEM_IMAGE


class BookMetadata:
    cache = {}

    @classmethod
    def get_cache(cls, book_path):
        book_Path = Path(book_path)

        key = str(book_path)

        book_time = book_Path.stat().st_mtime
        cached = cls.cache.get(key)

        # если нет cache или файл обновился
        if not cached or cached["book_time"] != book_time:
            print("🔥 Parsing epub (cache refresh)")
            metadata = get_epub_metadata(book_path)
            cls.cache[key] = {
                "book_time": book_time,
                "book_title": metadata[0],
                "book_creator": metadata[1],
                "description": metadata[2],
                "cover_image": metadata[3],
            }
        return cls.cache[key]






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
