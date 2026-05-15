import io
import os

from aiogram import Router, F
from aiogram.filters import Command
from aiogram.filters.command import CommandObject
from aiogram.types import Message, FSInputFile

from Services.Converters import *
from Services.Reader import Reader

router_converter = Router(name='converter')


# Конверт аудио в текст с помощью Whisper
# @router_converter.message(F.voice)
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

        result = model.transcribe(
            temp_ogg_path,
            # language="ru",
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


@router_converter.message(Command('trans'))
async def handler(message: Message):
    how_translate = message.text.split(' ')[0]
    if message.reply_to_message:
        eng_text = await translator(message.reply_to_message.text)
    elif message.quote:
        eng_text = await translator(message.quote.text)
    else:
        eng_text = await translator(message.text)

    if eng_text:
        await message.reply(f'{eng_text}')
    else:
        await message.answer('Текст не обнаружен, вставьте его после команды!')


@router_converter.message(Command('convert'))
async def handler(message: Message, command: CommandObject, reader:Reader):
    msg = await message.answer('Подготавливаю аудио...')

    text = command.args

    if message.reply_to_message:  # Если просто текст в АУДИО перевести когда репли делаешь
        if message.reply_to_message.text:  # Если просто текст в АУДИО перевести когда репли делаешь
            text = message.reply_to_message.text

        elif message.reply_to_message.caption:  # Если подпись под картинкой
            text = message.reply_to_message.caption

    if text:
        name_file = make_title(text)
        await convert_text_audio(text, name_file + ".mp3", reader.reading_speed)
        audio = FSInputFile(name_file + ".mp3")
        await message.reply_audio(
            audio=audio,
            performer=message.bot._me.first_name,
            title=name_file,
        )
        os.remove(audio.filename)

    else:
        await message.answer('Текст не обнаружен, вставьте его после команды!')

    await msg.delete()

# титул из текста
def make_title(text, words=6, max_len=60):
    clean = re.sub(r'[<>:"/\\|?*]', '', text)
    title = " ".join(clean.split()[:words])
    return title[:max_len]


def check_english_content(text, threshold=0.7):
    """
    Проверяет, является ли текст преимущественно английским
    Args:
        text: текст для проверки
        threshold: порог (0.7 = 70% английских символов)
    """
    if not text:
        return False
    # Считаем английские символы
    english_count = len(re.findall(r'[a-zA-Z]', text))
    total_chars = len(re.findall(r'[a-zA-Zа-яА-Я]', text))  # только буквы
    if total_chars == 0:
        return False
    ratio = english_count / total_chars
    return ratio >= threshold

    # """Проверяет, содержит ли текст английские символы"""
    # bool(re.search(r'[а-яА-Я]', text))
