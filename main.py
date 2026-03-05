import logging
import asyncio

from aiogram import Dispatcher, Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand
from argostranslate import package

from Middlewares.Data import Middleware_typing
from SQL.RR import ReadRepository
from Services.Library import Library
from Services.Reader import Sender, PATH_READ_DB
from Services.Scheduler import scheduler, Scheduler

from Handlers.Book_universal import universal_router
from Handlers.Start_service import start_router
from Handlers.Converters import convert_router
from Handlers.Book import book_router

from config import Config, load_config

import whisper
import argostranslate.package
import argostranslate.translate

# Конфигурация и логирование
config: Config = load_config()

logging.basicConfig(
    level=logging.INFO,
    style='{',
    format='#[{asctime}] #{levelname} | {name} | : "{message}"'
)

logger = logging.getLogger(__name__)
logger.info("Start bot!")

bot = Bot(
    token=config.tg_bot.token,
    default=DefaultBotProperties(parse_mode='Markdown')
)

dispatcher = Dispatcher()
dispatcher.update.middleware(Middleware_typing())
# dispatcher.callback_query.middleware(Middleware_callback())

dispatcher.include_router(start_router)
dispatcher.include_router(convert_router)
dispatcher.include_router(book_router)
dispatcher.include_router(universal_router)


async def set_bot_commands():
    commands = [
        BotCommand(command="/start", description="Приветствую!"),
        BotCommand(command="/book", description="Читаю книги на английском"),
        BotCommand(command="/ru_en", description="Перевод (RU / EN)"),
        BotCommand(command="/en_ru", description="Перевод (EN / RU)"),
        BotCommand(command="/audio_eng", description="Текст в аудио (EN)"),
        BotCommand(command="/audio_ru", description="Текст в аудио (RU)"),
    ]
    await bot.set_my_commands(commands)


# Загружаем модель для распознавания РЕЧИ (по умолчанию используется GPU, если доступен)
async def set_whisper():
    model = whisper.load_model("base")
    dispatcher["model"] = model


# Устанавливаем АРГО транслятор
async def set_argostranslate():
    # Обновляем индекс пакетов
    argostranslate.package.update_package_index()
    available_packages = argostranslate.package.get_available_packages()

    # Пакет ru->en
    package_ru_en = next((p for p in available_packages if p.from_code == "ru" and p.to_code == "en"), None)
    if package_ru_en:
        argostranslate.package.install_from_path(package_ru_en.download())
        print("Пакет ru->en установлен")
    else:
        print("Пакет ru->en не найден")

    # Пакет en->ru
    package_en_ru = next((p for p in available_packages if p.from_code == "en" and p.to_code == "ru"), None)
    if package_en_ru:
        argostranslate.package.install_from_path(package_en_ru.download())
        print("Пакет en->ru установлен")
    else:
        print("Пакет en->ru не найден")


# Reader / Scheduler
async def set_reader():
    sender_service = Sender(bot)
    dispatcher["sender"] = sender_service

    rr = ReadRepository(PATH_READ_DB)
    Scheduler.restore_all_jobs(sender_service, rr)
    scheduler.start()


async def main():
    await set_bot_commands()
    await set_argostranslate()
    await set_whisper()

    await set_reader()
    library1 = Library(PATH_READ_DB)
    library1.sync_library()

    logger.info("Bot polling started")
    await dispatcher.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
