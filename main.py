import logging
import asyncio

from aiogram import Dispatcher, Bot
from aiogram.client.default import DefaultBotProperties
from aiogram.types import BotCommand
from argostranslate import package

from Middlewares.mw1 import Middleware_typing, Middleware_access_maintenenace
from Services.Library import Library
from Services.Reader import Sender
from Services.Scheduler import scheduler, Scheduler

from Handlers.Universal import router_universal
from Handlers.Maintenance import router_maintenance
from Handlers.Converters import router_converter
from Handlers.Book import router_book

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

    # session = AiohttpSession(proxy='socks5://127.0.0.1:12334')
    bot = Bot(
        token=config.tg_bot.token,
        default=DefaultBotProperties(parse_mode='Markdown'),
        # session=session
    )

    dispatcher = Dispatcher()

    dispatcher.message.middleware(Middleware_typing())
    dispatcher.callback_query.middleware(Middleware_typing())

    router_maintenance.message.middleware(Middleware_access_maintenenace())
    router_maintenance.callback_query.middleware(Middleware_access_maintenenace())

    dispatcher.include_router(router_maintenance)
    dispatcher.include_router(router_converter)
    dispatcher.include_router(router_book)
    dispatcher.include_router(router_universal)


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

    installed_languages = argostranslate.translate.get_installed_languages()

    def is_installed(from_code, to_code):
        try:
            from_lang = next(l for l in installed_languages if l.code == from_code)
            to_lang = next(l for l in installed_languages if l.code == to_code)
            from_lang.get_translation(to_lang)
            return True
        except Exception:
            return False

    codes = {lang.code for lang in installed_languages}

    # если одного из языков нет — точно нужно ставить
    if not ("ru" in codes and "en" in codes):
        need_ru_en = True
        need_en_ru = True
    else:
        need_ru_en = not is_installed("ru", "en")
        need_en_ru = not is_installed("en", "ru")

    if not (need_ru_en or need_en_ru):
        print("Все пакеты уже установлены")
        return

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


# Scheduler
async def set_scheduler():
    sender = Sender(bot)
    dispatcher["sender"] = sender

    Scheduler(sender)
    scheduler.start()






async def main():
    await set_bot()
    await set_bot_commands()
    await set_argostranslate()
    await set_scheduler()

    library1 = Library()
    library1.sync_library()

    logger.info("Bot polling started")

    try:
        async with bot:
            await bot.delete_webhook(drop_pending_updates=True)
            await dispatcher.start_polling(bot, drop_pending_updates=True)
    except Exception as e:
        await bot.session.close()
        logger.error(f"❌ Ошибка подключения: {e}", exc_info=True)
        input("Нажми Enter чтобы не закрывать консоль...")




if __name__ == "__main__":

        asyncio.run(main())

