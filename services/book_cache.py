from services.reader_engine import epub_paragraph_generator


class BookCache:

    cache = {}

    @classmethod
    def get_paragraphs(cls, book_path):

        key = str(book_path)

        if key not in cls.cache:

            print("🔥 Parsing epub FIRST TIME")

            cls.cache[key] = list(
                epub_paragraph_generator(book_path)
            )

        return cls.cache[key]