import logging
import asyncio

from aiogram import Dispatcher, Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand
from argostranslate import package

from Middlewares.mw1 import Middleware_typing
from SQL.RR_sql import ReadRepository
from Services.Library import Library
from Services.Reader import Sender
from Services.Scheduler import scheduler, Scheduler

from Handlers.Universal import universal_router
from Handlers.Maintenance import start_router
from Handlers.Converters import convert_router
from Handlers.Book import book_router

from config import Config, load_config

import whisper
import argostranslate.package
import argostranslate.translate

from aiogram.client.session.aiohttp import AiohttpSession

# Конфигурация и логирование
config: Config = load_config()

logging.basicConfig(
    level=logging.INFO,
    style='{',
    format='#[{asctime}] #{levelname} | {name} | : "{message}"'
)

logger = logging.getLogger(__name__)
logger.info("Start bot!")

dispatcher: Dispatcher
bot: Bot


async def set_bot():
    global dispatcher, bot

    session = AiohttpSession(proxy='socks5://127.0.0.1:12334')
    bot = Bot(
        token=config.tg_bot.token,
        default=DefaultBotProperties(parse_mode='Markdown'),
        session=session
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
    sender1 = Sender(bot)
    dispatcher["sender"] = sender1

    rr = ReadRepository()
    Scheduler.restore_all_jobs(sender1, rr)
    scheduler.start()


async def main():
    await set_bot()
    await set_bot_commands()
    await set_argostranslate()
    await set_whisper()

    await set_reader()
    library1 = Library()
    library1.sync_library()  # Проверяет папку Books и добавляет отсутствующие книги в SQL

    logger.info("Bot polling started")
    await bot.delete_webhook(drop_pending_updates=True)  # очистка всех старых апдейтов
    await dispatcher.start_polling(bot, drop_pending_updates=True)


if __name__ == "__main__":
    asyncio.run(main())
