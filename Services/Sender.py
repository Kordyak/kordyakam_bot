
import math
import os
from aiogram import Bot
from aiogram.types import FSInputFile, BufferedInputFile
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB

from Locales.translator import t
from Services.Converters import convert_text_audio, translator
from Services.Reader import Reader


# Отправитель
class Sender:
    def __init__(self, bot: Bot):
        self.bot = bot

    async def send_chunk(self, reader:Reader):
        chunk = reader.get_next_chunk()
        user_id = reader.user_id

        msg_end_book = t(reader.lang_interface, 'donate_me', username=reader.username, book_title=reader.book_title)
        if not chunk:
            await self.bot.send_message(user_id, msg_end_book, parse_mode='HTML')
            return

        if len(chunk.splitlines()) == 1:
            paragraph = str(reader.paragraph_indx)
        else:
            paragraph = f'{reader.paragraph_indx - len(chunk.splitlines()) + 1}...{reader.paragraph_indx}'

        # caption, translate_chunk = await asyncio.gather(
        #     convert_text_audio(chunk + " End of paragraph.", paragraph + ".mp3", reader.reading_speed, reader.voice),
        #     translator(chunk)
        # )
        caption = await convert_text_audio(chunk + " End of paragraph.", paragraph + ".mp3", reader.reading_speed, reader.voice)

        start_caption = f'{reader.book_creator} / <b>"{reader.book_title}"</b> / ({reader.progress}%)'
        caption = f"{start_caption}\n{caption}"

        audio = FSInputFile(paragraph + ".mp3")
        duration = math.ceil(MP3(audio.filename).info.length)

        # МИНИНАТЮРУ картинку вставляем
        # if reader.cover_image:
            # rewrite_mp3_tags(audio.filename, reader) # К файлу привязываем ТЭГИ заголовок, создатель
            # thumbnail = make_thumbnail(reader.cover_image) # Миниатюра картинки для бота
            # await asyncio.gather(
            #     asyncio.to_thread(rewrite_mp3_tags, audio.filename, reader),
            #     asyncio.to_thread(make_thumbnail, reader.cover_image),
            # )

        # ПАРАМЕТРЫ для аудио сообщения
        audio_kwargs = dict(
            chat_id=user_id,
            audio=audio,
            thumbnail=reader.thumbnail,
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
            caption = f"{start_caption}\n{chunk}"
            await self.bot.send_message(
                chat_id=user_id,
                text=caption,
                parse_mode="HTML",
            )

        # Отправляем скрытый перевод
        translate_chunk = await translator(chunk)
        await self.bot.send_message(
            chat_id=user_id,
            text=f"<tg-spoiler>{translate_chunk}</tg-spoiler>",
            parse_mode="HTML",
        )

        os.remove(audio.filename) # удаляем аудио

        if reader.paragraph_indx == reader.total_paragraphs:
            await self.bot.send_message(user_id, msg_end_book, parse_mode='HTML')


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


