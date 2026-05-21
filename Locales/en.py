TEXTS = {
    # ================= Button =================

    "btn_book_info": '📖 Description "{title}"',
    "btn_change_time": '⏰ Change time ({time})',
    "btn_change_speed": '🏃‍➡️ Change speed ({speed})%',
    "btn_change_voice": '🎙️ Change voice ({voice})',
    "btn_change_paragraph": '🔖 Read from another paragraph',
    "btn_delete_book": '❌ Delete "{title}"',

    "btn_library": "📚 Library",
    "btn_upload_book": "📖 Upload your book",
    "btn_reader_menu": "⚙️ Reader menu",
    "btn_next_paragraph": "▶️ Read next paragraph",

    "btn_book_description": "ℹ️ Book description",
    "btn_upload_library_book": "⬇️ Uploading a book to read?",

    # ================= START =================
    "start_no_book": 'Hello, <b>{first_name}</b>!'
                     '\nLet’s choose a <b>book from the library</b>.'
                     '\n/library_en'
                     '\n/library_ru'
                     '\nOr you can upload your own <b>.epub</b> file.'
                     '\n/upload',
    "start_with_book": 'Reader menu:'
                       '\nYou are reading now: <b>"{book_title}"</b>'
                       '\nLast paragraph: <b>{paragraph_indx}</b>'
                       '\nReading progress: <b>{progress}%</b>',

    # ================= LIBRARY =================
    "library_empty": "The library is empty for now 📚",
    "library_choose": "\n\nEnter the book number to select it for reading or viewing details.",
    "book_selected": "You selected:"
                     "\n{i}. {creator} / <b>{title}</b>"
                     "\nOr choose another book by entering a different number.",
    "invalid_book_number": "Invalid book number. Press cancel to exit.",
    "paragraph": "paragraphs: ",

    # Description
    "invalid_book": "😈 It looks like you haven't downloaded the book",

    # Загрузка собственной книги
    "upload_book": 'Submit your EPUB file 📚 for download',
    "upload_error": '😅 This is not an epub',
    "upload_too_large": "😅 File is too large. Maximum 10 MB",
    "exist_book": 'This book is already in my database 📚',

    # ================= BOOK SET =================
    "book_set": 'Book <b>"{book_title}"</b> has been set.'
                "\nYou can set the time to receive the paragraph each day over reader menu /start."
                "\nOr get the paragraph by requesting /next",

    # ================= TIME =================
    "change_time": '⏰ The paragraph is currently being sent at <b>{time}</b>.'
                    '\nTo change:'
                    '\nSend the time in <code>HH:MM</code> format.',
    "invalid_time": "😈 Invalid time format. Use HH:MM",
    "time_saved": "⏰ Paragraph delivery time set: {time}"
                  "\nScheduler enabled ✅"
                  "\nYou can request a paragraph now with the /next command.",

    # ================= SPEED =================
    "speed_current": "🏃‍➡️ Your current reading speed is {speed}%\nYou can adjust it between 50 and 150 (clarity range)",
    "speed_invalid": "😈 You probably entered letters. Use a number from 50 to 150",
    "speed_saved": "🏃‍➡️ Reading speed changed: {speed}%",

    # ================= VOICE =================
    "voice_select": "🎙 Choose a voice for book's text-to-speech",
    "voice_set": "🎙 Selected voice: {voice}",

    # ================= PARAGRAPH =================
    "paragraph_input": "Enter the paragraph number to start reading from."
                       "\nEnter a number from 1 to {total}",
    "no_book": "You don't have a book selected.",
    "paragraph_only_number": "Please enter a number only",
    "paragraph_range": "Enter a number between 1 and {total}",
    "paragraph_updated": "✅ Paragraph index updated!",

    # ================= DELETE =================
    "delete_confirm": "Are you sure?",

    # Language
    "select_language": '🌐 Select language.'
                       '\nNow installed <b>english</b>.',
    "set_language": '🌐 English language is installed.',

    # DONATE
    'donate_me': "Congratulations, {username}!"
                 "\nLooks like you've finished reading{book_title}!"
                 "\nI suggest you choose a new book from my <b>library...</b>"
                 "\n\n<b>I accept gifts and donations</b> for a cup of tea ⛾ :)"
                 "\n You can send me TG stars...★★★",

}