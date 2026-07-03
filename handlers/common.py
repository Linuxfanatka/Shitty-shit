"""
handlers/common.py

Базовые команды: /start и /help. Как и все остальные хэндлеры,
доступны только владельцу бота (см. modules/auth.restricted).
"""

from telegram import Update
from telegram.ext import ContextTypes

from modules.auth import restricted

START_TEXT = (
    "Привет! Я твой личный AI-ассистент.\n\n"
    "Вот что я умею:\n"
    "/news — собрать и проанализировать свежие новости из твоих RSS-лент\n"
    "/weather — узнать погоду и получить совет по одежде\n"
    "/ask <вопрос> — задать мне произвольный вопрос\n"
    "/help — показать это сообщение\n\n"
    "Также я сам присылаю дайджест новостей и сводку по погоде по расписанию, "
    "если это включено в настройках (.env: AUTO_NEWS_ENABLED / AUTO_WEATHER_ENABLED)."
)


@restricted
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(START_TEXT)


@restricted
async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(START_TEXT)
