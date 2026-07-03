"""
modules/auth.py

Проверка доступа: бот реагирует ТОЛЬКО на Telegram-аккаунт с ID,
указанным в переменной окружения TELEGRAM_ALLOWED_USER_ID.

Все остальные пользователи полностью игнорируются: бот не отправляет
им никакого ответа (ни отказа, ни сообщения об ошибке) — попытка
обращения просто записывается в лог сервера для твоей информации.
"""

import functools
import logging

from telegram import Update
from telegram.ext import ContextTypes

from config import TELEGRAM_ALLOWED_USER_ID

logger = logging.getLogger(__name__)


def restricted(handler):
    """
    Декоратор для хэндлеров команд: пропускает к выполнению только владельца
    бота (TELEGRAM_ALLOWED_USER_ID). Для всех остальных — тихий игнор.
    """

    @functools.wraps(handler)
    async def wrapper(update: Update, context: ContextTypes.DEFAULT_TYPE, *args, **kwargs):
        user = update.effective_user
        if user is None or user.id != TELEGRAM_ALLOWED_USER_ID:
            logger.warning(
                "Игнорирую сообщение от постороннего пользователя: id=%s, username=%s",
                getattr(user, "id", None),
                getattr(user, "username", None),
            )
            return  # полный игнор, никакого ответа в чат
        return await handler(update, context, *args, **kwargs)

    return wrapper
