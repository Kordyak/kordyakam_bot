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
        # deep-translator sync -> выносим в отдельный поток
        result = await asyncio.to_thread(
            gt1.translate,
            text
        )
        return result

    except Exception as e:
        msg = f"😢 Ошибка перевода: {e}"
        print(msg)
        return msg



    # "ru-RU-DmitryNeural"  # Самый популярный мужской RU голос. Спокойный и очень разборчивый.
    # "ru-RU-PavelNeural"  # Чуть более живой и эмоциональный.
    # "ru-RU-SvetlanaNeural"  # мягкая подача

    # "en-US-GuyNeural"  # Очень чистый американский голос.
    # "en-US-AndrewNeural"  # Более спокойный и "дикторский".
    # "en-US-BrianNeural"  # Хорошо подходит для книг и long-text. // СУПЕР ГОЛОС

    # "en-US-JennyNeural"  # один из самых популярных женских голосов // ОТСТОЙ
    # "en-US-AriaNeural"  # более выразительный и живой // ТАКСЕБЕ, высокий
    # "en-US-AnaNeural"  # мягкий и довольно естественный // Детский отстой
    # "en-GB-SoniaNeural"  # британский акцент, спокойное чтение /// ПРИЯТНЫЙ !!!!
async def convert_text_audio(text: str, path_mp3: str, speed) -> str | None:
    text = re.sub('https.*', '', string=text)
    # Генерация mp3
    lang = detect_lang_simple(text)
    rate = f"{speed-100:+d}%"
    if lang == "ru":
        communicate = edge_tts.Communicate(text=text, voice="ru-RU-SvetlanaNeural",rate=rate)
    else:
        communicate = edge_tts.Communicate(text=text,voice="en-GB-SoniaNeural",rate=rate)

    # СОхраняем mp3 и создаем тайминги одновременно. В поток можно обратиться один раз для чтения или записи
    timestamps = []
    with open(path_mp3, "wb") as f:
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












# # Function to check internet connectivity
# def is_internet_available():
#     try:
#         # Try to connect to a reliable external server
#         requests.get("https://www.google.com", timeout=5)
#         return True
#     except requests.ConnectionError:
#         return False
#
#
# # Retry settings
# MAX_RETRIES = 60  # Maximum number of retry attempts
# RETRY_DELAY = 60  # Delay between retries in seconds
#
#
# async def send_with_retry(bot, chat_id, text, max_retries=MAX_RETRIES, delay=RETRY_DELAY):
#     """
#     Send a message with retry logic in case of connection errors.
#     """
#     for attempt in range(max_retries):
#
#         try:
#             if not is_internet_available():
#                 logger.warning(f"No internet connection. Retrying in {delay} seconds...")
#                 await asyncio.sleep(delay)
#                 continue
#
#             # if '_' in text:
#             await bot.send_message(chat_id=chat_id,
#                                    text=text,
#                                    parse_mode='HTML')
#             # else:
#             # await bot.send_message(chat_id=chat_id, text=text)
#             logger.info(f"Message sent to {chat_id}")
#             break  # Exit the loop if the message is sent successfully
#
#         except Exception as e:
#             logger.error(f"Attempt {attempt + 1} failed: {e}")
#             if attempt < max_retries - 1:  # Don't wait on the last attempt
#                 await asyncio.sleep(delay)
#             else:
#                 logger.error(f"Max retries reached. Failed to send message to {chat_id}")




