import logging
import asyncio

import edge_tts
from aiogram import Dispatcher, Bot
from aiogram.client.default import DefaultBotProperties

from Middlewares.mw1 import MiddlewareUsers, MiddlewareAdmin
from Services.Library import Library
from Services.Sender import Sender
from Services.Scheduler import scheduler, Scheduler
from Handlers.Confirm import router_universal
from Handlers.Service import router_service
from Handlers.Converters import router_converter
from Handlers.Book import router_book
from config import Config, load_config, MYPROXY

config: Config = load_config()

logging.basicConfig(
    level=logging.INFO,
    style='{',
    format='#[{asctime}] #{levelname} | {name} | : "{message}"'
)

logger = logging.getLogger(__name__)


dispatcher: Dispatcher
bot: Bot


async def set_bot():
    global dispatcher, bot
    # session = AiohttpSession(proxy=f"socks5://{MYPROXY}")
    bot = Bot(
        token=config.tg_bot.token,
        default=DefaultBotProperties(parse_mode='Markdown'),
        # session=session
    )
    # Users
    dispatcher = Dispatcher()
    dispatcher.message.outer_middleware(MiddlewareUsers())
    dispatcher.callback_query.outer_middleware(MiddlewareUsers())
    # Admin
    router_service.message.middleware(MiddlewareAdmin())
    router_service.callback_query.middleware(MiddlewareAdmin())
    dispatcher.include_router(router_service)

    dispatcher.include_router(router_converter)
    dispatcher.include_router(router_book)
    dispatcher.include_router(router_universal)


async def set_scheduler():
    sender = Sender(bot)
    dispatcher["sender"] = sender
    Scheduler(sender)
    scheduler.start()



async def list_voices():
    voices = await edge_tts.list_voices()
    for voice in voices:
        print(
            voice["ShortName"],
            "|",
            voice["Gender"],
            "|",
            voice["Locale"]
        )


async def main():
    # await list_voices()
    await set_bot()
    await set_scheduler()

    library1 = Library()
    library1.sync_library()

    async with bot:
        await bot.delete_webhook()
        await dispatcher.start_polling(bot)


if __name__ == "__main__":
        asyncio.run(main())

