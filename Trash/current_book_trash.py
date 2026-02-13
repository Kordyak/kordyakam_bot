
class Current_book:

    TELEGRAM_LIMIT = 1000

    def __init__(self, book_path, state_file):
        self.book_title, self.book_author = get_epub_metadata(book_path)
        self.book_path = book_path
        self.state_file = Path(state_file)
        # Загружаем все параграфы
        self.paragraphs = list(epub_paragraph_generator(book_path))
        # текущий индекс
        self.index = self.load_state()
        self.index_all = len(self.paragraphs)


    @property
    def progress(self):
        if self.index_all == 0:
            return 0
        return round((self.index / self.index_all) * 100, 1)

    # =====================
    # STATE
    # =====================

    def load_state(self):
        if self.state_file.exists():
            data = json.loads(self.state_file.read_text())
            return data.get("index", 0)
        return 0

    def save_state(self):
        self.state_file.write_text(json.dumps({"index": self.index}))

    # =====================
    # GET NEXT CHUNK
    # =====================

    def get_next_chunk(self, min_len=300):

        if self.index >= len(self.paragraphs):
            return None

        buffer = ""

        # собираем параграфы пока не наберём минимум
        while self.index < len(self.paragraphs):

            paragraph = self.paragraphs[self.index]

            buffer += ("\n" if buffer else "") + paragraph
            self.index += 1

            if len(buffer) >= min_len:
                break

        self.save_state()

        # режем только если превышен telegram limit
        return smart_telegram_split(buffer.strip(), self.TELEGRAM_LIMIT)