import asyncio
import logging

import requests
from telethon import events, TelegramClient

from aiogram import Dispatcher, Bot, F
from aiogram.client.default import DefaultBotProperties
from aiogram.types import Message, BotCommand, FSInputFile

from config import *
from services.service_1 import check_word, translate_rus_eng, convert_text_audio
from handlers import handler_1

import argostranslate.package



logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    style='{',
                    format='#[{asctime}] #{levelname} | {name} | : "{message}"')
logger.info(f'Start bot!')

config: Config = load_config()

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)

client = TelegramClient('kord1', config.client.api_id, config.client.api_hash, device_model="MS Windows", system_version="11")
client.session.save()
client.start()



bot = Bot(token=config.tg_bot.token,
          default=DefaultBotProperties(parse_mode='MARKDOWN'))
commands = [
    #BotCommand(command="/start", description="Запустить бота"),
    BotCommand(command="/ru_en", description="Перевод русcко-английский"),
    BotCommand(command="/en_ru", description="Перевод англо-русский"),
    BotCommand(command="/audio", description="Конвертировать текст в аудио на англ."),
]


async def set_bot_commands():
    await bot.set_my_commands(commands)

loop.create_task(set_bot_commands())

dp = Dispatcher()
dp.include_router(handler_1.router)

loop.create_task(dp.start_polling(bot))


languages_to_install = ['en', 'ru']  # Add more language codes as needed

argostranslate.package.update_package_index()
available_packages = argostranslate.package.get_available_packages()
package_to_install = next(filter(lambda x: x.from_code == "ru" and x.to_code == "en", available_packages))
argostranslate.package.install_from_path(package_to_install.download())

dp['client'] = client
# dp['argostranslate'] = argostranslate


@client.on(events.NewMessage(chats=channels_id))
async def handler(event: events):
    key: str = check_word(event.message.text, key_words)
    if key:
        message_link = f"https://t.me/{event.message.chat.username}/{event.message.id}"
        eng_text = translate_rus_eng(event.message.text)
        # await bot.send_message(chat_id=chat_id_IA, text=f'{eng_text}\n{message_link}')
        await send_with_retry(bot, chat_id_IA, f'{eng_text}\n{message_link}')


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

            await bot.send_message(chat_id=chat_id, text=text)
            logger.info(f"Message sent to {chat_id}")
            break  # Exit the loop if the message is sent successfully
        except Exception as e:
            logger.error(f"Attempt {attempt + 1} failed: {e}")
            if attempt < max_retries - 1:  # Don't wait on the last attempt
                await asyncio.sleep(delay)
            else:
                logger.error(f"Max retries reached. Failed to send message to {chat_id}")

if __name__ == "__main__":
    try:
        client.run_until_disconnected()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        logger.info("Bot stopped.")




