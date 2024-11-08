from aiogram import Router, types, filters, Bot
import os
from telethon import TelegramClient
from services.service import old_news

router = Router()



@router.message(filters.Command(commands=['parsing_channel']))
async def old_news_handler(message: types.Message, bot: Bot, client: TelegramClient):
    await old_news(message, bot, client)

@router.message(lambda m: m.text.isdigit() and len(m.text) == 6)
async def run_rdp(message: types.Message):
    os.system(f"Run_rdp.exe {message.text}")
    os.system(f"start call_process_by_time.lnk")


@router.message(lambda m: m.text == '/shutdown')
async def shutdown_pc(message: types.Message):
    if message.text.split(" ")[1] == 's':
        os.system(f"shutdown /s")
    elif message.text.split(" ")[1] == 'h':
        os.system(f"shutdown /h")
    elif message.text.split(" ")[1] == 'r':
        os.system(f"shutdown /r")
