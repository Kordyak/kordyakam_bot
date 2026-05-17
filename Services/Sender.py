import asyncio
import math
import os
from io import BytesIO
from aiogram import Bot
from aiogram.types import FSInputFile, BufferedInputFile
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB
from PIL import Image

from Services.Converters import convert_text_audio, translator
from Services.Reader import Reader


# Отправитель
class Sender:
    def __init__(self, bot: Bot):
        self.bot = bot

    async def send_chunk(self,user_id:int, reader:Reader):
        chunk = reader.get_next_chunk()

        msg_end_book = (
            f'Поздравляю {reader.username}! Похоже ты дочитал "{reader.book_title}"!'
            "\nПредлагаю выбрать новую книгу из моей <b>библиотеки...</b>"
            "\n\n<b>Принимаю дары и донаты</b> на чашечку ⛾ :)"
            "\n<tg-spoiler>СБП Яндекс"
            "\n+79177537768</tg-spoiler>"
        )

        if not chunk:
            await self.bot.send_message(user_id,msg_end_book, parse_mode='HTML')
            return

        if len(chunk.splitlines()) == 1:
            paragraph = str(reader.paragraph_indx)
        else:
            paragraph = f'{reader.paragraph_indx - len(chunk.splitlines()) + 1}...{reader.paragraph_indx}'

        caption, translate_chunk = await asyncio.gather(
            convert_text_audio(chunk + " End of paragraph.", paragraph + ".mp3", reader.reading_speed, reader.voice),
            translator(chunk)
        )


        caption = (
            f'{reader.book_creator} / <b>"{reader.book_title}"</b>'
            f"\n({reader.progress}%)"
            f"\n{caption}"
        )
        long_caption = (
            f'{reader.book_creator} / <b>"{reader.book_title}"</b>'
            f"\n({reader.progress}%)"
            f"\n{chunk}"
        )

        audio = FSInputFile(paragraph + ".mp3")
        duration = math.ceil(MP3(audio.filename).info.length)
        rewrite_mp3_tags(audio.filename, reader) # К файлу привязываем ТЭГИ заголовок, создатель
        thumbnail = make_thumbnail(reader.cover_image) # Миниатюра картинки для бота

        # ПАРАМЕТРЫ для аудио сообщения
        audio_kwargs = dict(
            chat_id=user_id,
            audio=audio,
            thumbnail=thumbnail,
            performer=reader.book_title,
            title=paragraph,
            duration=duration,
            parse_mode="HTML"
        )

        # АУДИО вместе caption если помещается в 1024
        if len(caption) <= 1024:
            audio_kwargs["caption"] = caption

        await self.bot.send_audio(**audio_kwargs)

        # ЕСЛИ длинный caption отдельным сообщением
        if len(caption) > 1024:
            await self.bot.send_message(
                chat_id=user_id,
                text=long_caption,
                parse_mode="HTML",
            )

        # Отправляем скрытый перевод
        await self.bot.send_message(
            chat_id=user_id,
            text=f"<tg-spoiler>{translate_chunk}</tg-spoiler>",
            parse_mode="HTML",
        )

        os.remove(audio.filename) # удаляем аудио

        if reader.paragraph_indx == reader.total_paragraphs:
            await self.bot.send_message(user_id,msg_end_book, parse_mode='HTML')


# К файлу привязываем ТЭГИ заголовок, создатель
def rewrite_mp3_tags(file_path: str, reader):
    tags = ID3()
    tags.add(APIC(
        encoding=3,
        mime="image/jpeg",
        type=3,
        desc="Cover",
        data=reader.cover_image
    ))
    tags.add(TIT2(encoding=3, text=reader.book_title))
    tags.add(TPE1(encoding=3, text=reader.book_creator))
    tags.add(TALB(encoding=3, text=reader.book_title))
    tags.save(file_path, v2_version=3)


# Миниатюру из аудио файла для сообщения
def make_thumbnail(image_bytes: bytes) -> BufferedInputFile:
    with Image.open(BytesIO(image_bytes)) as img:
        img = img.convert("RGB")
        img.thumbnail((320, 320))

        output = BytesIO()
        quality = 85
        while True:
            output.seek(0)
            output.truncate()
            img.save(output, format="JPEG", quality=quality, optimize=True)
            if output.tell() <= 200 * 1024 or quality <= 40:
                break
            quality -= 5

        return BufferedInputFile(file=output.getvalue(), filename="thumb.jpg")