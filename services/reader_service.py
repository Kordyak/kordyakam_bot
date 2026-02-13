class ReaderService:

    cache = {}

    @classmethod
    def get_reader(cls, user_id):

        if user_id in cls.cache:
            return cls.cache[user_id]

        book_path = UserManager.get_book_path(user_id)
        state_path = UserManager.get_state_path(user_id)

        reader = Current_book(book_path, state_path)

        cls.cache[user_id] = reader

        return reader
