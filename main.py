import logging
import re
import os
import requests
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import yt_dlp

# Настройка логирования
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# Опции для yt-dlp
YDL_OPTS = {
    'format': 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best',
    'outtmpl': '%(id)s.%(ext)s',
    'cookiefile': 'cookies.txt',
    'noplaylist': True,
    'quiet': False,
    'no_warnings': False,
    'ignoreerrors': False,
    'merge_output_format': 'mp4',
    'http_headers': {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
}

# Telegram лимит (50 МБ)
TELEGRAM_MAX_SIZE = 50 * 1024 * 1024  # 50 МБ в байтах

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик команды /start"""
    await update.message.reply_text(
        "Привет! Я бот для скачивания видео с Twitter (X), включая NSFW. "
        "Отправь мне ссылку на твит с видео (например, https://x.com/username/status/123456789). "
        "Файлы больше 50 МБ отправляются как ссылка, если у тебя нет Telegram Premium."
    )

def upload_to_catbox(file_path):
    """Загрузка файла на catbox.moe и возврат ссылки"""
    try:
        url = "https://catbox.moe/user/api.php"
        data = {
            'reqtype': 'fileupload',
            'userhash': ''  # Анонимная загрузка
        }
        with open(file_path, 'rb') as f:
            files = {'fileToUpload': f}
            response = requests.post(url, data=data, files=files)
            if response.status_code == 200 and response.text.startswith('https://'):
                return response.text.strip()
        logger.error(f"Ошибка загрузки на catbox: {response.text}")
        return None
    except Exception as e:
        logger.error(f"Ошибка загрузки на catbox: {e}")
        return None

async def download_video(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик текстовых сообщений с ссылками"""
    url = update.message.text.strip()

    # Проверка формата ссылки
    if not re.match(r'https?://(twitter|x)\.com/\w+/status/\d+', url):
        await update.message.reply_text(
            "Пожалуйста, отправь корректную ссылку на твит с видео (например, https://x.com/username/status/123456789)."
        )
        return

    await update.message.reply_text("Проверяю видео...")

    try:
        with yt_dlp.YoutubeDL(YDL_OPTS) as ydl:
            # Извлечение информации о видео
            info = ydl.extract_info(url, download=False)
            video_id = info.get('id', 'video')
            video_title = info.get('title', f'Video_{video_id}')

            # Проверка размера видео (приблизительно)
            video_size_bytes = info.get('filesize') or info.get('filesize_approx')
            if video_size_bytes and video_size_bytes > TELEGRAM_MAX_SIZE:
                await update.message.reply_text(
                    f"Видео слишком большое ({video_size_bytes / (1024 * 1024):.2f} МБ). "
                    "Я скачаю его и отправлю ссылку для скачивания."
                )

            # Скачивание видео
            await update.message.reply_text("Скачиваю видео...")
            ydl.download([url])

            # Поиск скачанного файла
            video_file = f"{video_id}.mp4"
            if not os.path.exists(video_file):
                await update.message.reply_text(
                    "Не удалось найти скачанный файл. Возможно, видео недоступно или cookies не дают доступ."
                )
                return

            # Проверка размера файла
            file_size = os.path.getsize(video_file)
            if file_size <= TELEGRAM_MAX_SIZE:
                # Попробуем отправить как видео
                try:
                    with open(video_file, 'rb') as video:
                        await update.message.reply_video(
                            video=video,
                            caption=f"{video_title}",
                            supports_streaming=True
                        )
                    await update.message.reply_text("Видео успешно отправлено!")
                except Exception as e:
                    logger.warning(f"Не удалось отправить как видео: {e}, пробую как документ...")
                    # Попробуем отправить как документ
                    with open(video_file, 'rb') as doc:
                        await update.message.reply_document(
                            document=doc,
                            caption=f"{video_title}"
                        )
                    await update.message.reply_text("Видео отправлено как файл!")
                os.remove(video_file)
                return

            # Файл слишком большой, загружаем на catbox.moe
            await update.message.reply_text(
                f"Файл слишком большой ({file_size / (1024 * 1024):.2f} МБ) для Telegram. "
                "Загружаю на внешний хостинг..."
            )
            download_url = upload_to_catbox(video_file)
            os.remove(video_file)

            if download_url:
                await update.message.reply_text(
                    f"Видео слишком большое для Telegram. Скачай его здесь: {download_url}\n"
                    "Если у тебя есть Telegram Premium, бот может отправлять файлы до 2 ГБ."
                )
            else:
                await update.message.reply_text(
                    "Не удалось загрузить видео на внешний хостинг. Попробуй другое видео или уменьши размер."
                )

    except yt_dlp.utils.DownloadError as de:
        logger.error(f"Ошибка yt-dlp: {de}")
        error_msg = (
            "Не удалось скачать видео. Возможные причины:\n"
            "- Видео ограничено (NSFW, приватное или удалено).\n"
            "- Cookies в cookies.txt устарели или не дают доступ к NSFW.\n"
            "Что сделать:\n"
            "1. Проверь, что аккаунт X в cookies имеет доступ к NSFW.\n"
            "2. Обнови cookies.txt.\n"
            "3. Убедись, что ссылка ведет на твит с видео.\n"
            f"Детали ошибки: {str(de)}"
        )
        await update.message.reply_text(error_msg)
    except Exception as e:
        logger.error(f"Общая ошибка: {e}")
        await update.message.reply_text(
            f"Произошла ошибка: {str(e)}. Проверь ссылку, cookies и попробуй снова."
        )

async def error_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработчик ошибок"""
    logger.error(f"Update {update} caused error {context.error}")
    if update and update.message:
        await update.message.reply_text("Произошла ошибка. Проверь логи или попробуй снова.")

def main():
    """Запуск бота"""
    application = Application.builder().token('8126052267:AAG2jrP7z6SeBkNKEiJ_aOb-3sR_pTr9t_w').build()

    # Регистрация обработчиков
    application.add_handler(CommandHandler("start", start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, download_video))
    application.add_error_handler(error_handler)

    # Запуск бота
    application.run_polling()

if __name__ == '__main__':
    main()
