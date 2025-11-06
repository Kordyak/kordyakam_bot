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

    text = re.sub(r"[\*\[\]]", "", text)  #удаляем символы
    text = re.sub(r"\(https.*?\)", "", text).strip()  #удаляем ссылки из текста

    if re.match('/en_ru',how_translate) :
        return argostranslate.translate.translate(text, "en", "ru")
    elif  re.match('/ru_en',how_translate):
        return argostranslate.translate.translate(text, "ru", "en")


def convert_text_audio(in_text: str, name_file: str = "") -> FSInputFile:
    text = re.sub('https.*', '', string=in_text)
    audio = gTTS(text=text, lang="en", slow=True)
    if name_file == "" :
        name_file = f"{text[:15]}.mp3"
        name_file = re.sub(r"[\n]", '', name_file)  #удаляем символы
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
MAX_RETRIES = 120  # Maximum number of retry attempts
RETRY_DELAY = 15  # Delay between retries in seconds


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
            if '_' in text:
                await bot.send_message(chat_id=chat_id, text=text, parse_mode=None)
            else:
                await bot.send_message(chat_id=chat_id, text=text)
            logger.info(f"Message sent to {chat_id}")
            break  # Exit the loop if the message is sent successfully

        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:  # Don't wait on the last attempt
                await asyncio.sleep(delay)
            else:
                logger.error(f"Max retries reached. Failed to send message to {chat_id}")