

@router.message(F.document)
async def receive_epub(message: Message, state: FSMContext):

    if not message.document.file_name.endswith(".epub"):
        return

    await state.update_data(file_id=message.document.file_id)

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="Да", callback_data="confirm_book")]
    ])

    await message.answer("Загрузить книгу?", reply_markup=kb)

    await state.set_state(UploadBook.waiting_confirm)


@router.callback_query(F.data=="confirm_book")
async def confirm_book(callback: CallbackQuery, state: FSMContext, bot: Bot):

    data = await state.get_data()
    file = await bot.get_file(data["file_id"])

    path = UserManager.get_book_path(callback.from_user.id)

    await bot.download_file(file.file_path, destination=path)

    await callback.message.answer("Во сколько отправлять? Пример: 06:30")

    await state.set_state(UploadBook.waiting_time)




@router.callback_query(F.data.in_(["upload_book","replace_book"]))
async def upload_book_start(callback: CallbackQuery, state: FSMContext):

    await callback.message.answer("Отправь EPUB файл 📚")

    await state.set_state(UploadBook.waiting_epub)



@router.message(UploadBook.waiting_epub, F.document)
async def receive_epub(message: Message, state: FSMContext, bot: Bot):

    if not message.document.file_name.endswith(".epub"):
        await message.answer("Это не epub 😅")
        return

    user_id = message.from_user.id

    path = UserManager.get_book_path(user_id)

    file = await bot.get_file(message.document.file_id)

    await bot.download_file(file.file_path, destination=path)

    # ВАЖНО — очистить cache reader
    ReaderService.cache.pop(user_id, None)

    await message.answer("Книга загружена 😈")


@router.callback_query(F.data=="current_book")
async def show_book(callback: CallbackQuery):

    reader = ReaderService.get_reader(callback.from_user.id)

    await callback.message.answer(
        f"📖 {reader.book_author} — {reader.book_title}\n"
        f"Прогресс: {reader.progress}%"
    )

