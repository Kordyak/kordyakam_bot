
from telethon import TelegramClient

dp['client'] = client

#Клиент моей телеграм уз
client = TelegramClient(
    'kord1',
    config.client.api_id,
    config.client.api_hash,
    device_model="MS Windows",
    system_version="11",
)





# Слушает новости МЕДУЗА, Милов
@client.on(events.NewMessage(chats=channels))
async def handler(event: events):
    rus_text = event.message.raw_text
    key: str = check_word(rus_text, key_words)
    if key:
        link = f"🔗 t.me/{event.chat.username}/{event.message.id}"
        eng_text = translate_rus_eng(rus_text, '/ru_en')
        mix_text = Mix_text(eng_text, rus_text)
        # await bot.send_message(chat_id=chat_id_IA, text=f'{eng_text}\n{link}')
        await send_with_retry(bot, chat_id_IA, f'{mix_text}\n{link}')

# Слушает обзоры книг на английском
@client.on(events.NewMessage(chats=channels_english_book))
async def handler(event: events):
    text = event.message.raw_text
    match = re.search(r'Description:\s*(.*?)\s*Read book', text, re.DOTALL)

    #Текст из чата про книги
    if match:
        text_match = match.group(1).strip()
        if check_english_content(text_match):  # Проверяет, является ли текст преимущественно английским
            text_rus = translate_rus_eng(text_match, "/en_ru")
            book_name = text.split("\n")[0]
            audio_file: FSInputFile = convert_text_audio(text_match, book_name, "en")
            link = f"🔗 t.me/{event.chat.username}/{event.message.id}"
            await bot.send_audio(chat_id= chat_id_IA,
                                 audio= audio_file,
                                 performer=bot._me.first_name,
                                 title=book_name,
                                 caption= f"{text_match}\n"
                                          f"{link}",
                                 parse_mode = 'HTML'
                                 )
            await bot.send_message(chat_id= chat_id_IA,
                                    text=f"<tg-spoiler>{text_rus}</tg-spoiler>",
                                    parse_mode = 'HTML')
            os.remove(audio_file.filename)
        else:
            await bot.send_message(chat_id_IA, "Текст преимущественно (70%) не на английском!!!")




await client.start() # запускаем telethon внутри общего loop
