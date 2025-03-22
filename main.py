import os
import requests
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command
from dotenv import load_dotenv

load_dotenv()

BOT_TOKEN = os.getenv("BOT_TOKEN")
RAPIDAPI_KEY = os.getenv("RAPIDAPI_KEY")

bot = Bot(token=BOT_TOKEN)
dp = Dispatcher()

API_URL = "https://twitter-video-download.p.rapidapi.com/twitter"

@dp.message(Command("start"))
async def start(message: types.Message):
    await message.answer("Привет! Отправь ссылку на видео с Twitter, и я скачаю его для тебя.")

@dp.message()
async def handle_message(message: types.Message):
    url = message.text.strip()

    if "x.com" in url or "twitter.com" in url:
        await message.answer("⏳ Загружаю видео, подожди немного...")

        headers = {
            "X-RapidAPI-Key": RAPIDAPI_KEY,
            "X-RapidAPI-Host": "twitter-video-download.p.rapidapi.com"
        }

        params = {"url": url}
        response = requests.get(API_URL, headers=headers, params=params)

        if response.status_code == 200:
            video_url = response.json().get("download_url")
            if video_url:
                await message.answer_video(video_url, caption="✅ Вот твое видео!")
            else:
                await message.answer("❌ Не удалось найти видео.")
        else:
            await message.answer("❌ Ошибка при скачивании видео.")

    else:
        await message.answer("⚠ Отправь ссылку на видео из Twitter (X).")

