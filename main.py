import os
import yt_dlp
import asyncio
from aiogram import Bot, Dispatcher, types, Router
from aiogram.types import Message
from aiogram.filters import Command
from dotenv import load_dotenv

# Загружаем токен из .env
load_dotenv()
TOKEN = os.getenv("BOT_TOKEN")

bot = Bot(token=TOKEN)
dp = Dispatcher()
router = Router()
dp.include_router(router)

async def download_video(tweet_url):
    """Скачиваем видео с X (Twitter) в наилучшем качестве"""
    output_path = "video.mp4"
    ydl_opts = {
        "outtmpl": output_path,
        "format": "best",  # Максимальное качество
    }

    # Выполняем `yt-dlp` в фоне
    await asyncio.to_thread(lambda: yt_dlp.YoutubeDL(ydl_opts).download([tweet_url]))
    
    return output_path

@router.message(Command("start"))
async def start_cmd(message: Message):
    await message.reply("👋 Привет! Отправь мне ссылку на видео из X (Twitter), и я скачаю его в наилучшем качестве.")

@router.message(lambda message: "x.com" in message.text or "twitter.com" in message.text)
async def handle_twitter_video(message: Message):
    tweet_url = message.text.strip()
    status_message = await message.reply("⏬ Загружаю видео...")

    try:
        video_path = await download_video(tweet_url)  # ✅ Ждём завершения загрузки
        with open(video_path, "rb") as video:
            await message.reply_video(video)
        os.remove(video_path)  # Удаляем после отправки
    except Exception as e:
        await status_message.edit_text(f"❌ Ошибка: {e}")

@router.message()
async def unknown_message(message: Message):
    await message.reply("🚀 Отправь мне ссылку на видео из X (Twitter)!")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
