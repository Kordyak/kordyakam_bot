import asyncio
import imghdr
import math
import os
from pathlib import Path

from aiogram import Bot
from aiogram.types import FSInputFile, Message
from mutagen.mp3 import MP3
from mutagen.id3 import ID3, APIC, TIT2, TPE1, TALB

from Locales.translator import t
from Services.Converters import convert_text_audio, translator
from Services.PrefetchManager import PrefetchManager, PrefetchEntry
from Services.Reader import Reader


# Отправитель
class Sender:
    def __init__(self, bot: Bot):
        self.bot = bot

    async def send_chunk(self, reader:Reader):
        user_id = reader.user_id

        clock_msg = await self.bot.send_message(user_id, "⏳")
        msg_end_book = t(reader.lang_interface, 'donate_me', username=reader.username, book_title=reader.book_title)

        # 1️⃣ Есть готовый prefetch с теми же speed/voice?
        prefetched = PrefetchManager.get(user_id, reader.reading_speed, reader.voice, reader.paragraph_indx)

        if prefetched:
            new_index = prefetched.new_index
            chunk = prefetched.chunk
            caption = prefetched.caption
            translate_chunk = prefetched.translate_chunk
            mp3_path = prefetched.mp3_path
        else:
            chunk, new_index = reader.get_next_chunk()
            if not chunk:
                await self.bot.send_message(user_id, msg_end_book, parse_mode='HTML')
                return
            file_name = self._write_paragraphs(chunk, reader.paragraph_indx)
            mp3_path = f'Cache/{reader.user_id}/{file_name}.mp3'
            cache_dir = Path(f'Cache/{reader.user_id}')
            cache_dir.mkdir(parents=True, exist_ok=True)
            caption, translate_chunk = await asyncio.gather(
                convert_text_audio(chunk + t(reader.lang_interface, 'end_par'), mp3_path, reader.reading_speed, reader.voice),
                translator(chunk)
            )
        reader.db.save_i_chunk(user_id, new_index)  # ← сохраняем только здесь
        reader.paragraph_indx = new_index

        start_caption = f'{reader.book_creator} / <b>"{reader.book_title}"</b> / ({reader.progress}%)'
        caption = f"{start_caption}\n{caption}"

        if reader.cover_image:
            rewrite_mp3_tags(mp3_path, reader) # К файлу привязываем ТЭГИ, чтобы картинка была привязана к файлу, важно при проигрывании аудио в пуш уведомлении

        audio = FSInputFile(mp3_path)
        duration = math.ceil(MP3(mp3_path).info.length)
        # ПАРАМЕТРЫ для аудио сообщения
        audio_kwargs = dict(
            chat_id=user_id,
            audio=audio,
            thumbnail=reader.thumbnail,
            performer=reader.book_title,
            title=audio.filename,
            duration=duration,
            parse_mode="HTML"
        )

        # АУДИО вместе caption если помещается в 1024
        if len(caption) <= 1024:
            audio_kwargs["caption"] = caption

        try:
            await self.bot.send_audio(**audio_kwargs)
        finally:
            await clock_msg.delete()
            Path(mp3_path).unlink(missing_ok=True)

        # ЕСЛИ длинный caption отдельным сообщением
        if len(caption) > 1024:
            caption = f"{start_caption}\n{chunk}"
            await self.bot.send_message(
                chat_id=user_id,
                text=caption,
                parse_mode="HTML",
            )

        # Отправляем скрытый перевод
        await self.bot.send_message(
            chat_id=user_id,
            text=f"<tg-spoiler>{translate_chunk}</tg-spoiler>",
            parse_mode="HTML",
        )

        if reader.paragraph_indx == reader.total_paragraphs:
            await self.bot.send_message(user_id, msg_end_book, parse_mode='HTML')

        # 2️⃣ Запускаем фоновую предзагрузку следующего
        await self._prefetch_next(reader)

    @staticmethod
    def _write_paragraphs(chunk, last_index: int)-> str:
        if len(chunk.splitlines()) == 1:
            return str(last_index)
        else:
            return f'{last_index - len(chunk.splitlines()) + 1}...{last_index}'


    async def _prefetch_next(self, reader: Reader):
        user_id = reader.user_id
        last_index = reader.paragraph_indx
        chunk, new_index = reader.get_next_chunk()
        if not chunk:
            return
        file_name = self._write_paragraphs(chunk, new_index)
        mp3_path = f'Cache/{reader.user_id}/{file_name}.mp3'
        try:
            caption, translate_chunk = await asyncio.gather(
                convert_text_audio(chunk + t(reader.lang_interface, 'end_par'), mp3_path, reader.reading_speed, reader.voice),
                translator(chunk)
            )
            PrefetchManager.set(user_id, PrefetchEntry(
                last_index=last_index,
                new_index=new_index,
                chunk=chunk,
                caption=caption,
                translate_chunk=translate_chunk,
                speed=reader.reading_speed,
                voice=reader.voice,
                mp3_path=mp3_path,
            ))
        except Exception as e:
            print(f"⚠️ Prefetch failed user={user_id}: {e}")
            os.unlink(mp3_path) if os.path.exists(mp3_path) else None








# К файлу привязываем ТЭГИ заголовок, создатель
def rewrite_mp3_tags(file_path: str, reader: Reader):
    tags = ID3()

    mime = "image/jpeg"
    fmt = imghdr.what(None, h=reader.cover_image)
    if fmt == "png":
        mime = "image/png"

    tags.add(APIC(
        encoding=3,
        mime=mime,
        type=3,
        desc="Cover",
        data=reader.cover_image
    ))

    tags.add(TIT2(encoding=3, text=str(reader.paragraph_indx)))
    tags.add(TPE1(encoding=3, text=reader.book_creator))
    tags.add(TALB(encoding=3, text=reader.book_title))
    tags.save(file_path, v2_version=3)


