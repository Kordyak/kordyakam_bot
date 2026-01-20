import whisper
import io

from telethon import events, TelegramClient

from aiogram import Dispatcher, Bot, F
from aiogram.client.default import DefaultBotProperties

from config import *
from handlers.handler_1 import *

import argostranslate.package


logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    style='{',
                    format='#[{asctime}] #{levelname} | {name} | : "{message}"')
logger.info(f'Start bot!')

config: Config = load_config()

#Асинхронный цикл
loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

#Клиент моей телеграм уз
client = TelegramClient('kord1', config.client.api_id, config.client.api_hash, device_model="MS Windows", system_version="11")
client.start()

#Бот
bot = Bot(token=config.tg_bot.token, default=DefaultBotProperties(parse_mode='Markdown'))

#Устанавливаем команды
commands = [
    BotCommand(command="/ru_en", description="Перевод русcко-английский"),
    BotCommand(command="/en_ru", description="Перевод англо-русский"),
    BotCommand(command="/audio_eng", description="Конвертировать текст в аудио на англ."),
    BotCommand(command="/audio_ru", description="Конвертировать текст в аудио на рус."),
]
async def set_bot_commands():
    await bot.set_my_commands(commands)

loop.create_task(set_bot_commands())

# Диспечтер для прослушивания БОТА
dp = Dispatcher()
dp.include_router(router)
loop.create_task(dp.start_polling(bot))

# АРГО транслятор
argostranslate.package.update_package_index()
available_packages = argostranslate.package.get_available_packages()
package_to_install = next(filter(lambda x: x.from_code == "ru" and x.to_code == "en", available_packages))
argostranslate.package.install_from_path(package_to_install.download())

dp['client'] = client
# dp['argostranslate'] = argostranslate

# Загрузка модели Whisper
try:
    # Загружаем модель для распознавания (по умолчанию используется GPU, если доступен)
    model = whisper.load_model("base")
    logging.info(f"Модель Whisper успешно загружена.")
except Exception as e:
    logging.error(f"Не удалось загрузить модель Whisper: {e}")
    # Вы можете выйти или установить model = None, чтобы избежать ошибок.
    model = None


@client.on(events.NewMessage(chats=channels))# МЕДУЗА
async def handler(event: events):
    rus_text = event.message.raw_text
    key: str = check_word(rus_text, key_words)
    if key:
        link = f"🔗 t.me/{event.chat.username}/{event.message.id}"
        eng_text = translate_rus_eng(rus_text, '/ru_en')
        mix_text = Mix_text(eng_text, rus_text)
        # await bot.send_message(chat_id=chat_id_IA, text=f'{eng_text}\n{link}')
        await send_with_retry(bot, chat_id_IA, f'{mix_text}\n{link}')


@client.on(events.NewMessage(chats=channels_english_book)) # Книги на английском
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


@dp.message(F.voice)
async def voice_message_handler(message: types.Message):
    """Обрабатывает голосовые сообщения и переводит их в текст с помощью Whisper."""
    if not model:
        await message.reply("❌ Модель распознавания речи не загружена. Проверьте логи.")
        return

    await message.bot.send_chat_action(chat_id=message.chat.id, action="typing")

    # 1. Скачивание голосового сообщения
    file_id = message.voice.file_id
    file = await bot.get_file(file_id)
    file_path = file.file_path

    # Скачиваем файл в байты
    audio_data = io.BytesIO()
    await bot.download_file(file_path, audio_data)
    audio_data.seek(0)

    # Создаем временный файл для Whisper, так как он лучше работает с путями, чем с буферами
    temp_ogg_path = "temp_voice.ogg"

    try:
        # Сохраняем OGG-файл на диск
        with open(temp_ogg_path, "wb") as f:
            f.write(audio_data.read())

        # 2. Распознавание речи с помощью Whisper
        # Указываем `language="ru"` для повышения точности и скорости
        result = model.transcribe(
            temp_ogg_path,
            language="ru",
            # Дополнительный параметр, чтобы избежать "мусора"
            fp16=False # Раскомментируйте, если есть проблемы с GPU
        )

        text = result["text"]

        # 3. Отправка результата
        if text.strip():
            await message.reply(f"🎤 **Распознанный текст (Whisper):**\n`{text}`")
        else:
            await message.reply("😔 Извините, не удалось распознать речь (пустой результат).")

    except Exception as e:
        logging.error(f"Ошибка при обработке голосового сообщения с Whisper: {e}")
        await message.reply("❌ Произошла ошибка при обработке аудио.")

    finally:
        # 4. Очистка временного файла
        if os.path.exists(temp_ogg_path):
            os.remove(temp_ogg_path)


if __name__ == "__main__":
    try:
        client.run_until_disconnected()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        logger.info("Bot stopped.")




