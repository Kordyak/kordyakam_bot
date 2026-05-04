import logging
import re
import edge_tts
import argostranslate.translate

import requests
import asyncio

logger = logging.getLogger(__name__)


def translate_rus_eng(in_text: str, how_translate: str) -> str:
    if re.match(r"/en_ru", in_text) or re.match(r"/ru_en", in_text):
        arr = in_text.split(' ')[1:]
        text = " ".join(arr)
    else:
        text = in_text
    if re.match('/en_ru', how_translate):
        return argostranslate.translate.translate(text, "en", "ru")
    elif re.match('/ru_en', how_translate):
        return argostranslate.translate.translate(text, "ru", "en")


def clean_text(text: str) -> str:
    text = re.sub(r'[^\w\s.,!?;:()\-–—\"\']', '', text)  # Удаляет эмодзи и специальные символы
    text = re.sub(r"[\*\[\]_]", "", text)  # удаляем символы
    text = re.sub(r"\(https.*?\)", "", text).strip()  # удаляем ссылки из текста
    return text


def tokenize(text: str) -> list[str]:
    return re.findall(r"\w+", text.lower())


async def convert_text_audio(text: str, mp3_path: str, lang: str, rate = "-12%") -> str:
    text = re.sub('https.*', '', string=text)
    # text = re.sub(r'\.\.\.+', '.', text)
    # text = re.sub(r"(?<!\w)'|'(?!\w)", "", text)  # убирает ' в начале и конце каждого предложения.

    # voice = "ru-RU-DmitryNeural"  # Самый популярный мужской RU голос. Спокойный и очень разборчивый.
    # voice = "ru-RU-PavelNeural"  # Чуть более живой и эмоциональный.
    # voice = "en-US-GuyNeural"  # Очень чистый американский голос.
    # voice = "en-US-AndrewNeural"  # Более спокойный и "дикторский".
    # voice = "en-US-BrianNeural"  # Хорошо подходит для книг и long-text.

    # Генерация mp3
    if lang == "en":
        communicate = edge_tts.Communicate(text=text, voice="en-US-BrianNeural",rate=rate)
    else:
        communicate = edge_tts.Communicate(text=text, voice="ru-RU-PavelNeural")

    timestamps = []

    # сразу открываем mp3
    with open(mp3_path, "wb") as f:
        async for chunk in communicate.stream():
            if chunk["type"] == "audio":
                f.write(chunk["data"])
            elif chunk["type"] == "SentenceBoundary":
                timestamps.append((
                    chunk["offset"] / 10_000_000,
                    chunk["text"].strip()
                ))

    caption = build_caption(timestamps)
    return caption




def format_time(seconds: float) -> str:
    seconds = int(seconds)
    m = seconds // 60
    s = seconds % 60
    return f"{m}:{s:02d}"


def build_caption(timestamps) -> str:
    lines = []
    for t, sentence in timestamps:
        lines.append(f"{format_time(t)} {sentence}")
    return "\n".join(lines)










def check_word(news: str, words: list) -> str:  # парсинг новостей на слово
    for key in words:
        if re.search(key.lower(), news.lower()):
            return key


# Function to check internet connectivity
def is_internet_available():
    try:
        # Try to connect to a reliable external server
        requests.get("https://www.google.com", timeout=5)
        return True
    except requests.ConnectionError:
        return False


# Retry settings
MAX_RETRIES = 60  # Maximum number of retry attempts
RETRY_DELAY = 60  # Delay between retries in seconds


async def send_with_retry(bot, chat_id, text, max_retries=MAX_RETRIES, delay=RETRY_DELAY):
    """
    Send a message with retry logic in case of connection errors.
    """
    for attempt in range(max_retries):

        try:
            if not is_internet_available():
                logger.warning(f"No internet connection. Retrying in {delay} seconds...")
                await asyncio.sleep(delay)
                continue

            # if '_' in text:
            await bot.send_message(chat_id=chat_id,
                                   text=text,
                                   parse_mode='HTML')
            # else:
            # await bot.send_message(chat_id=chat_id, text=text)
            logger.info(f"Message sent to {chat_id}")
            break  # Exit the loop if the message is sent successfully

        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:  # Don't wait on the last attempt
                await asyncio.sleep(delay)
            else:
                logger.error(f"Max retries reached. Failed to send message to {chat_id}")





def Mix_text(eng_text, rus_text):
    """Смешиваем текст англ./скрытый рус"""
    eng_lines = eng_text.split('\n')
    rus_lines = rus_text.split('\n')

    result = []
    for i in range(max(len(eng_lines), len(rus_lines)) - 1):
        eng_line = eng_lines[i] if i < len(eng_lines) else ""
        rus_line = rus_lines[i] if i < len(rus_lines) else ""

        if rus_line.strip():
            result.append(f"{eng_line}\n\n<tg-spoiler><i>{rus_line}</i></tg-spoiler>\n")
        elif eng_line.strip():
            result.append(f"{eng_line}")

    return '\n'.join(result)
