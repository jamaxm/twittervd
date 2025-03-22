import os
import asyncio
import yt_dlp
from aiogram import Bot, Dispatcher, types
from aiogram.types import FSInputFile
from aiogram.filters import Command
from dotenv import load_dotenv

# Загружаем переменные окружения
load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
COOKIES_PATH = os.getenv("COOKIES_PATH")  # Путь к cookies

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

# Функция загрузки видео с Twitter
async def download_twitter_video(url):
    options = {
        "outtmpl": "video.mp4",  # Сохранение как video.mp4
        "format": "best",  # Лучшее качество
        "cookies": COOKIES_PATH,  # Передача cookies
    }

    with yt_dlp.YoutubeDL(options) as ydl:
        ydl.download([url])

# Обработчик команды /start
@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Привет! Отправь ссылку на видео с Twitter, и я скачаю его для тебя.")

# Обработчик ссылок
@dp.message()
async def handle_message(message: types.Message):
    url = message.text.strip()

    if "x.com" in url or "twitter.com" in url:
        await message.answer("⏳ Загружаю видео, подожди немного...")

        try:
            await download_twitter_video(url)
            video = FSInputFile("video.mp4")  # Исправленный вариант
            await message.answer_video(video, caption="✅ Вот твое видео!")
            os.remove("video.mp4")  # Удаляем файл после отправки

        except Exception as e:
            await message.answer(f"❌ Ошибка: {str(e)}")

    else:
        await message.answer("⚠ Отправь ссылку на видео из Twitter (X).")

# Запуск бота
async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
