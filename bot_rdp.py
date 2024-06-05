from aiogram import Bot, Dispatcher, filters, types

import config

bot = Bot(config.BOT_TOKEN2)
dp = Dispatcher()

@dp.message(lambda message: message.text)
async def run_rdp(message: types.Message):
