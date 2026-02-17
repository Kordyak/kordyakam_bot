from pathlib import Path

from bs4 import BeautifulSoup
from ebooklib import epub, ITEM_DOCUMENT


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

    title = title[0][0] if title else Path(book_path).stem
    creator = creator[0][0] if creator else ""

    return title, creator