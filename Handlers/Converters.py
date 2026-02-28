import io

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.filters.command import CommandObject
from aiogram.types import Message

from Services.Converters import *
from Services.Reader import make_title

convert_router = Router(name='converter')


# Обрабатывает голосовые сообщения и переводит их в текст с помощью Whisper
@convert_router.message(F.voice)
async def voice_message_handler(message: Message, model):
    """Обрабатывает голосовые сообщения и переводит их в текст с помощью Whisper."""
    if not model:
        await message.reply("❌ Модель распознавания речи не загружена. Проверьте логи.")
        return

    bot = message.bot

    temp_msg = await message.answer('Подготавливаю текст!')

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
            fp16=False  # Раскомментируйте, если есть проблемы с GPU
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

        await temp_msg.delete()


@convert_router.message(Command('ru_en', 'en_ru'))
async def handler(message: Message):
    how_translate = message.text.split(' ')[0]
    if message.reply_to_message:
        eng_text = translate_rus_eng(message.reply_to_message.text, how_translate)
    elif message.quote:
        eng_text = translate_rus_eng(message.quote.text, how_translate)
    else:
        eng_text = translate_rus_eng(message.text, how_translate)

    if eng_text:
        await message.reply(f'{eng_text}')
    else:
        await message.answer('Текст не обнаружен, вставьте его после команды!')


@convert_router.message(Command('audio_eng', 'audio_ru'))
async def handler(message: Message, command: CommandObject):
    temp_msg = await message.answer('Подготавливаю аудио!')

    text = command.args
    if message.reply_to_message:  # Если просто текст в АУДИО перевести когда репли делаешь
        if message.reply_to_message.text:  # Если просто текст в АУДИО перевести когда репли делаешь
            text = message.reply_to_message.text

        elif message.reply_to_message.caption:  # Текст из чата про книги в АУДИО (капча под картинкой)
            match = re.search(r'Description:\s*(.*?)\s*Read book', message.reply_to_message.caption, re.DOTALL)
            if match:
                text = match.group(1).strip()
            else:
                text = message.reply_to_message.caption

    if not check_english_content(text):  # Проверяет, является ли текст преимущественно английским
        await message.reply("Текст преимущественно (70%) не на английском!!!")

    if command.command == "audio_ru":
        lang = "ru"
    else:
        lang = "en"

    if text:

        name_file = make_title(text)
        audio_file: FSInputFile = convert_text_audio(text, name_file, lang)
        await message.reply_audio(audio_file,
                                  performer=message.bot._me.first_name,
                                  title=name_file,
                                  )
        os.remove(audio_file.filename)
    else:
        await message.answer('Текст не обнаружен, вставьте его после команды!')

    await temp_msg.delete()
