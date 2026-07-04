"""
bot.py

Точка входа Telegram-бота — личного AI-ассистента.

Запуск:
    python bot.py

Перед запуском обязательно скопируй .env.example в .env и заполни его
своими значениями (см. README.md для подробной инструкции).
"""

import logging

from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

from config import LOG_LEVEL, TELEGRAM_BOT_TOKEN
from handlers.ask import ask_command
from handlers.common import help_command, start
from handlers.news import news_command
from handlers.weather import weather_command
from modules.scheduler import setup_jobs
from handlers.personal import remember_command, train_command, traininfo_command

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=LOG_LEVEL,
)
# Понижаем "шумность" сторонних библиотек, оставляя INFO для нашего кода
logging.getLogger("httpx").setLevel(logging.WARNING)

logger = logging.getLogger(__name__)


async def error_handler(update: object, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Глобальный обработчик ошибок: логирует, но не роняет бота."""
    logger.error("Необработанная ошибка при обработке апдейта %s", update, exc_info=context.error)


def build_application() -> Application:
    application = Application.builder().token(TELEGRAM_BOT_TOKEN).build()

    application.add_handler(CommandHandler("start", start))
    application.add_handler(CommandHandler("help", help_command))
    application.add_handler(CommandHandler("news", news_command))
    application.add_handler(CommandHandler("weather", weather_command))
    application.add_handler(CommandHandler("ask", ask_command))
    application.add_handler(CommandHandler("remember", remember_command))
    application.add_handler(CommandHandler("train", train_command))
    application.add_handler(CommandHandler("traininfo", traininfo_command))

    application.add_error_handler(error_handler)

    setup_jobs(application)
    return application


def main() -> None:
    logger.info("Запускаю личного AI-ассистента…")
    application = build_application()
    application.run_polling(allowed_updates=Update.ALL_TYPES, drop_pending_updates=True)


if __name__ == "__main__":
    main()
