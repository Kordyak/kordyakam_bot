import os
from aiogram.types import FSInputFile
import logging
import re
from gtts import gTTS
import argostranslate.translate


logger = logging.getLogger(__name__)

def translate_rus_eng(in_text: str) -> str:
    en_ru: bool = False
    if re.match(r"/en_ru", in_text):
        en_ru = True
    if re.match(r"/en_ru", in_text) or re.match(r"/ru_en", in_text) :
        arr = in_text.split(' ')[1:]
        text = " ".join(arr)
    else:
        text = in_text

    result_re = re.sub(r"[\*\[\]]", "", text)  #удаляем символы
    result_re = re.sub(r"\(https.*?\)", "", result_re).strip()  #удаляем ссылки из текста

    if en_ru:
        return argostranslate.translate.translate(result_re, "en", "ru")
    else:
        return argostranslate.translate.translate(result_re, "ru", "en")


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
