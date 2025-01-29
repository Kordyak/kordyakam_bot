import os
from aiogram.types import FSInputFile
from gtts import gTTS
import logging
from googletrans import Translator
import re

logger = logging.getLogger(__name__)


def translate_rus_eng(in_text: str) -> str:
    result_re = re.sub(r"[\*\[\]]", "", in_text)  #удаляем символы
    result_re = re.sub(r"\(https.*?\)", "", result_re)  #удаляем ссылки из текста
    translator = Translator()
    result_translate = translator.translate(text=result_re, src='ru', dest='en')
    return result_translate.text


def convert_text_audio(in_text: str) -> FSInputFile:
    text = re.sub('https.*', '', string=in_text)
    audio = gTTS(text=text, lang="en", slow=True)
    name_file = f"{text[:15]}.mp3"
    name_file = re.sub(r"[\n]", '', name_file)  #удаляем символы
    audio.save(name_file)
    return FSInputFile(path=os.path.join(name_file))


def check_word(news: str, words: list) -> str:  # парсинг новостей на слово
    for key in words:
        if re.search(key, news.lower()):
            return key
