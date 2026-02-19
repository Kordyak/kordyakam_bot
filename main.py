from pathlib import Path

from Services.Library import Library
from config import Config, load_config
import logging

import asyncio
from aiogram import Dispatcher, Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand

import whisper
import argostranslate.package

from Handlers.start_hand import start_router
from Handlers.converter_hand import convert_router
from Handlers.book_hand import book_router
from Services.Reader import Sender

from Services.Scheduler import scheduler, Scheduler

# Загружаем конфигурацию
config: Config = load_config()

# Включаем Лог
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    style='{',
                    format='#[{asctime}] #{levelname} | {name} | : "{message}"')
logger.info(f'Start bot!')


bot = Bot(
    token=config.tg_bot.token,
    default=DefaultBotProperties(parse_mode='Markdown')
)

# Диспетчер для прослушивания БОТА
dispatcher = Dispatcher()
dispatcher.include_router(start_router)
dispatcher.include_router(convert_router)
dispatcher.include_router(book_router)

# Устанавливаем команды
async def set_bot_commands():
    commands = [
        BotCommand(command="/start", description="Приветствую!"),
        BotCommand(command="/book", description="Читаю книги на английском"),
        BotCommand(command="/ru_en", description="Перевод русско-английский"),
        BotCommand(command="/en_ru", description="Перевод англо-русский"),
        BotCommand(command="/audio_eng", description="Конвертировать текст в аудио на англ."),
        BotCommand(command="/audio_ru", description="Конвертировать текст в аудио на рус."),
    ]
    await bot.set_my_commands(commands)


# Устанавливаем АРГО транслятор
async def set_argostranslate():
    argostranslate.package.update_package_index()
    available_packages = argostranslate.package.get_available_packages()
    package_to_install = next(filter(lambda x: x.from_code == "ru" and x.to_code == "en", available_packages))
    argostranslate.package.install_from_path(package_to_install.download())


# Загружаем модель для распознавания РЕЧИ (по умолчанию используется GPU, если доступен)
model = whisper.load_model("base")
dispatcher["model"] = model

async def set_reader():
    sender_service = Sender(bot)
    dispatcher["sender"] = sender_service

    Scheduler.restore_all_jobs(sender_service)
    scheduler.start()





async def main():
    await set_bot_commands()
    await set_argostranslate()
    await set_reader()
    Library.sync_library()
    await dispatcher.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())




