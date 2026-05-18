import logging
import re
import edge_tts
from deep_translator import GoogleTranslator
import asyncio

logger = logging.getLogger(__name__)

async def translator(in_text: str) -> str:
    # если текст начинается с команды
    if re.match(r"^/(en_ru|ru_en)", in_text):
        text = " ".join(in_text.split()[1:])
    else:
        text = in_text

    text = text.strip()

    if not text:
        return ""

    lang = detect_lang_simple(text)

    if lang == "ru":
        gt1 = GoogleTranslator(source='ru', target='en')
    else:
        gt1 = GoogleTranslator(source='en', target='ru')

    try:
        # выносим в отдельный поток
        result = await asyncio.to_thread(gt1.translate,text)
        return result
    except Exception as e:
        msg = f"😢 Ошибка перевода: {e}"
        print(msg)
        return msg


async def convert_text_audio(text: str, path_mp3: str, speed:int, voice: str) -> str | None:
    text = re.sub(r'https?://\S+', '', text)
    if not text:
        return None

    lang = detect_lang_simple(text)
    rate = f"{speed - 100:+d}%"

    if lang == "ru":
        if voice == "":
            voice = 'en-US-BrianNeural'
        communicate = edge_tts.Communicate(text=text, voice=voice,rate=rate)
    else:
        if voice == "":
            voice = 'ru-RU-SvetlanaNeural'
        communicate = edge_tts.Communicate(text=text,voice=voice,rate=rate)

    # СОхраняем mp3 и создаем тайминги одновременно. В поток можно обратиться один раз для чтения или записи
    timestamps = []
    with open(path_mp3, "wb") as f:
        try:
            async for chunk in communicate.stream():
                if chunk["type"] == "audio":
                    f.write(chunk["data"])
                elif chunk["type"] == "SentenceBoundary":
                    timestamps.append((
                        chunk["offset"] / 10_000_000,
                        chunk["text"].strip()
                    ))
        except edge_tts.exceptions.NoAudioReceived:
            return None
    caption = build_caption(timestamps)
    return caption
def build_caption(timestamps) -> str:
    lines = []
    for t, sentence in timestamps:
        lines.append(f"{format_time(t)} {sentence}")
    return "\n".join(lines)
def format_time(seconds: float) -> str:
    seconds = int(seconds)
    m = seconds // 60
    s = seconds % 60
    return f"{m}:{s:02d}"



def detect_lang_simple(text):
    ru_chars = len(re.findall(r'[а-яА-ЯёЁ]', text))
    en_chars = len(re.findall(r'[a-zA-Z]', text))

    return "ru" if ru_chars > en_chars else "en"




