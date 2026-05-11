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

    dispatcher.message.outer_middleware(Middleware_typing())
    dispatcher.callback_query.outer_middleware(Middleware_typing())

    router_maintenance.message.middleware(Middleware_access_maintenenace())
    router_maintenance.callback_query.middleware(Middleware_access_maintenenace())

    dispatcher.include_router(router_maintenance)
    dispatcher.include_router(router_converter)
    dispatcher.include_router(router_book)
    dispatcher.include_router(router_universal)


async def set_bot_commands():
    commands = [
        BotCommand(command="/start", description="Немного обо мне"),
        BotCommand(command="/ru_en", description="Перевод (RU/EN)"),
        BotCommand(command="/en_ru", description="Перевод (EN/RU)"),
        BotCommand(command="/audio_eng", description="Текст -> аудио (EN)"),
        BotCommand(command="/audio_ru", description="Текст -> аудио (RU)"),
    ]
    await bot.set_my_commands(commands)


async def set_scheduler():
    sender = Sender(bot)
    dispatcher["sender"] = sender

    Scheduler(sender)
    scheduler.start()


async def main():
    try:
        await set_bot()
        await set_bot_commands()
        await set_scheduler()

        library1 = Library()
        library1.sync_library()

        async with bot:
            await bot.delete_webhook(drop_pending_updates=True)
            await dispatcher.start_polling(bot, drop_pending_updates=True)
            logger.info("Bot polling started")

    except Exception as e:
        await bot.session.close()
        input("Нажми Enter чтобы закрыть консоль...")


if __name__ == "__main__":
        asyncio.run(main())

