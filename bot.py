from telethon import TelegramClient, events
import config
import asyncio

from handlers.handler1 import send_message_IA, parsing_old_message



channel_source = [
    'https://t.me/channelOut2',
    'https://t.me/meduzalive',
    'https://t.me/LipsitsIgor',
    'https://t.me/bdtprb',
]

loop = asyncio.new_event_loop()
asyncio.set_event_loop(loop)
client = TelegramClient('kord', config.api_id, config.api_hash, loop=loop)
client.start()

@client.on(events.NewMessage(chats=channel_source))  # Слушает каналы на сообщение
async def handler(event):
    await send_message_IA(event.message)  # Отправляет сообщение через бота в группу ИА
    await parsing_old_message(client)


if __name__ == '__main__':
    # loop.create_task(parsing_old_message(client))  # добавляет задание в ЦИКЛ
    client.run_until_disconnected()















# loop.create_task(parsing_old_message(client))  # Парсер старых сообщений