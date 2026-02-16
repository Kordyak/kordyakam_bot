
import os

from aiogram import Router, F
from aiogram.types import Message

router = Router(name='rdp')

# start RDP
@router.message(F.text.regexp(r"^\d{6}$"))
async def run_rdp(message: Message):
    os.system(f"start call_process_by_time.exe {message.text}")