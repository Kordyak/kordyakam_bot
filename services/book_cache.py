from pathlib import Path

from bs4 import BeautifulSoup
from ebooklib import epub, ITEM_DOCUMENT, ITEM_COVER, ITEM_IMAGE


class BookCache:

    cache = {}

    @classmethod
    def get_cache(cls, book_path):

        book_path = Path(book_path)

        key = str(book_path)
        mtime = book_path.stat().st_mtime

        cached = cls.cache.get(key)

        # =========================
        # если нет cache или файл обновился
        # =========================
        if not cached or cached["mtime"] != mtime:

            print("🔥 Parsing epub (cache refresh)")

            cls.cache[key] = {
                "mtime": mtime,
                "paragraphs": list(epub_paragraph_generator(book_path)),
                "metadata": get_epub_metadata(book_path),
            }

        return cls.cache[key]



def epub_paragraph_generator(epub_path):
    book = epub.read_epub(str(epub_path))
    for item in book.get_items_of_type(ITEM_DOCUMENT):
        soup = BeautifulSoup(item.get_content(), "html.parser")
        for p in soup.find_all("p"):
            text = p.get_text(strip=True)
            if text:
                yield text


def get_epub_metadata(book_path):
    book = epub.read_epub(str(book_path))

    title = book.get_metadata('DC', 'title')
    creator = book.get_metadata('DC', 'creator')
    description = book.get_metadata('DC', 'description')

    title = title[0][0] if title else Path(book_path).stem
    creator = creator[0][0] if creator else "нет создателя"
    description = description[0][0] if description else "нет описания"

    cover_image = get_cover(book)

    return title, creator, description, cover_image





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
