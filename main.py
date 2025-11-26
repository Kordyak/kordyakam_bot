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
    BotCommand(command="/audio_eng", description="Конвертировать текст в аудио на англ."),
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


@client.on(events.NewMessage(chats=channels))
async def handler(event: events):
    rus_text = event.message.raw_text
    key: str = check_word(rus_text, key_words)
    if key:
        link = f"🔗 t.me/{event.chat.username}/{event.message.id}"
        eng_text = translate_rus_eng(rus_text, '/ru_en')
        mix_text = Mix_text(eng_text, rus_text)
        # await bot.send_message(chat_id=chat_id_IA, text=f'{eng_text}\n{link}')
        await send_with_retry(bot, chat_id_IA, f'{mix_text}\n{link}')


@client.on(events.NewMessage(chats=channels_english_book))
async def handler(event: events):
    text = event.message.raw_text
    match = re.search(r'Description:\s*(.*?)\s*Read book', text, re.DOTALL)

    #Текст из чата про книги
    if match:
        text_match = match.group(1).strip()
        text_match = re.sub(r'[^\w\s.,!?;:()\-–—\"\']', '', text_match) #Удаляет эмодзи и специальные символы
        if check_english_content(text_match):  # Проверяет, является ли текст преимущественно английским
            text_rus = translate_rus_eng(text_match, "/en_ru")
            book_name = text.split("\n")[0]
            audio_file: FSInputFile = convert_text_audio(text_match, book_name)
            link = f"🔗 t.me/{event.chat.username}/{event.message.id}"
            await bot.send_audio(chat_id= chat_id_IA,
                                 audio= audio_file,

                                 performer=bot._me.first_name,
                                 title=book_name,
                                 caption= f"{text_match}\n"
                                          f"{link}")
            await bot.send_message(chat_id= chat_id_IA,
                                    text=f"<tg-spoiler>{text_rus}</tg-spoiler>",
                                    parse_mode = 'HTML')
            os.remove(audio_file.filename)
        else:
            await bot.send_message(chat_id_IA, "Текст преимущественно (70%) не на английском!!!")



if __name__ == "__main__":
    try:
        client.run_until_disconnected()
    except Exception as e:
        logger.error(f"Fatal error: {e}")
    finally:
        logger.info("Bot stopped.")




