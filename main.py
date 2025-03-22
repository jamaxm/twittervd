import os
import yt_dlp
import snscrape.modules.twitter as sntwitter
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
router = Router()  # Новый router
dp.include_router(router)  # Подключаем router

def get_video_url(tweet_url):
    """Получаем ссылку на видео из твита"""
    try:
        tweet_id = tweet_url.split("/")[-1]
        tweet = next(sntwitter.TwitterTweetScraper(tweet_id).get_items(), None)
        if tweet and tweet.media:
            for media in tweet.media:
                if isinstance(media, sntwitter.Video):
                    return media.variants[-1]["url"]
    except Exception as e:
        print(f"Ошибка: {e}")
    return None

async def progress_hook(d):
    """Обновляем статус скачивания"""
    if d["status"] == "downloading":
        percent = d.get("_percent_str", "0%")
        await bot.send_chat_action(chat_id=d["message"].chat.id, action=types.ChatAction.TYPING)
        await d["message"].edit_text(f"⏬ Загрузка видео... {percent}")

def download_video(video_url, message):
    """Скачиваем видео с наилучшим качеством"""
    output_path = "video.mp4"
    ydl_opts = {
        "outtmpl": output_path,
        "format": "bestvideo+bestaudio/best",  # Максимальное качество
        "merge_output_format": "mp4",
        "progress_hooks": [lambda d: asyncio.run(progress_hook({**d, "message": message}))],
    }
    with yt_dlp.YoutubeDL(ydl_opts) as ydl:
        ydl.download([video_url])
    return output_path

@router.message(Command("start"))  # Используем router
async def start_cmd(message: Message):
    await message.reply("👋 Привет! Отправь мне ссылку на твит с видео, и я скачаю его в наилучшем качестве.")

@router.message(lambda message: "twitter.com" in message.text)  # Используем router
async def handle_twitter_video(message: Message):
    tweet_url = message.text.strip()
    status_message = await message.reply("🔍 Ищу видео...")

    video_url = get_video_url(tweet_url)
    if not video_url:
        await status_message.edit_text("❌ Видео не найдено. Убедитесь, что ссылка верна.")
        return

    await status_message.edit_text("⏬ Загружаю видео в наилучшем качестве...")
    video_path = download_video(video_url, status_message)

    await message.reply_video(video=open(video_path, "rb"))
    os.remove(video_path)

@router.message()  # Используем router
async def unknown_message(message: Message):
    await message.reply("🚀 Отправь мне ссылку на видео из Twitter!")

async def main():
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
