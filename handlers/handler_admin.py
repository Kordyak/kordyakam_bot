from aiogram import Router, types, filters
import os


router = Router()



@router.message(lambda m: m.text.isdigit() and len(m.text) == 6)
async def run_rdp(message: types.Message):
    os.system(f"Run_rdp.exe {message.text}")


@router.message(lambda m: m.text == '/shutdown')
async def run_rdp(message: types.Message):
    if message.text.split(" ")[1] == 's':
        os.system(f"shutdown /s")
    elif message.text.split(" ")[1] == 'h':
        os.system(f"shutdown /h")
    elif message.text.split(" ")[1] == 'r':
        os.system(f"shutdown /r")
