from idlelib.replace import replace

from telethon import events, TelegramClient

from aiogram import Dispatcher, Bot, F
from aiogram.client.default import DefaultBotProperties

from config import *
from services.service_1 import *
from handlers.handler_1 import *

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
client.start()

bot = Bot(token=config.tg_bot.token, default=DefaultBotProperties(parse_mode='Markdown'))
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
dp.include_router(router)

loop.create_task(dp.start_polling(bot))

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
        username = event.message.chat.username

        if '_' in username:
            username = username.replace('_', '\\_')

        message_link = f"https://t.me/{username}/{event.message.id}"
        eng_text = translate_rus_eng(event.message.text, '/ru_en')
        # await bot.send_message(chat_id=chat_id_IA, text=f'{eng_text}\n{message_link}')
        await send_with_retry(bot, chat_id_IA, f'{eng_text}\n{message_link}')


if __name__ == "__main__":
    try:
        client.run_until_disconnected()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        logger.info("Bot stopped.")




