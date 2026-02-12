from pathlib import Path
from config import Config, load_config
import logging

import asyncio
from aiogram import Dispatcher, Bot, F
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand

import whisper
from Epub import send_daily_text, ReaderService
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import argostranslate.package

from handlers.handler_1 import router

# Загружаем конфигурацию
config: Config = load_config()

# Включаем Логгера
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO,
                    style='{',
                    format='#[{asctime}] #{levelname} | {name} | : "{message}"')
logger.info(f'Start bot!')


bot = Bot(
    token=config.tg_bot.token,
    default=DefaultBotProperties(parse_mode='Markdown')
)

# Диспечтер для прослушивания БОТА
dp = Dispatcher()
dp.include_router(router)

# Устанавливаем команды
async def set_bot_commands():
    commands = [
        BotCommand(command="/ru_en", description="Перевод русcко-английский"),
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
dp["model"] = model


# Устанавливаем планировщик для чтения книги по расписанию
async def read_book_on_schedule():
    EPUB_FILE = Path(__file__).parent / "books" / "Black_Beauty-Anna_Sewell.epub"
    reader = ReaderService(EPUB_FILE)
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        send_daily_text,
        "cron",
        hour=7,
        minute=0,
        args=[bot, reader]
    )
    scheduler.start()
    # await send_daily_text(bot,reader) # отправка первого чанка КНИГИ при запуске для проверки



async def main():
    await set_bot_commands()
    await set_argostranslate()
    await read_book_on_schedule()
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())




