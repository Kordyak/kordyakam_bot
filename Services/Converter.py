import os
from aiogram.types import FSInputFile
import logging
import re
from gtts import gTTS
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


def Clean_text(text: str) -> str:
    text = re.sub(r'[^\w\s.,!?;:()\-–—\"\']', '', text)  # Удаляет эмодзи и специальные символы
    text = re.sub(r"[\*\[\]_]", "", text)  # удаляем символы
    text = re.sub(r"\(https.*?\)", "", text).strip()  # удаляем ссылки из текста
    return text


def convert_text_audio(in_text: str, name_file: str, lang: str) -> FSInputFile:
    text = re.sub('https.*', '', string=in_text)
    if lang == "en":
        audio = gTTS(text=text, lang=lang, slow=True)
    else:
        audio = gTTS(text=text, lang=lang)

    audio.save(name_file)
    return FSInputFile(path=os.path.join(name_file))


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
