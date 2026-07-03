"""
modules/telegram_utils.py

Вспомогательные функции для отправки сообщений в Telegram:
- разбивка длинных сообщений на части (лимит Telegram — 4096 символов);
- безопасная отправка с HTML-разметкой и fallback на обычный текст,
  если сгенерированный нейросетью HTML вдруг окажется невалидным
  (Telegram в этом случае просто отклоняет всё сообщение).
"""

import logging
import re

from telegram import Bot
from telegram.constants import ParseMode
from telegram.error import BadRequest

logger = logging.getLogger(__name__)

TELEGRAM_MESSAGE_LIMIT = 4000  # с запасом от реального лимита Telegram в 4096

_TAG_RE = re.compile(r"<[^>]+>")


def _strip_html(text: str) -> str:
    return _TAG_RE.sub("", text)


def split_message(text: str, limit: int = TELEGRAM_MESSAGE_LIMIT) -> list[str]:
    """Делит длинный текст на части по границам строк, не разрывая слова/теги."""
    if len(text) <= limit:
        return [text]

    parts: list[str] = []
    current = ""
    for line in text.split("\n"):
        candidate = f"{current}\n{line}" if current else line
        if len(candidate) > limit:
            if current:
                parts.append(current)
            current = line
        else:
            current = candidate
    if current:
        parts.append(current)
    return parts


async def safe_send(bot: Bot, chat_id: int, text: str) -> None:
    """
    Отправляет сообщение с HTML-разметкой (как просят системные промпты).
    Если Telegram не может разобрать HTML из ответа модели (бывает при
    кривых/незакрытых тегах), отправляет ту же часть уже как обычный
    текст без тегов — пользователь в любом случае получит содержимое.
    """
    for chunk in split_message(text):
        try:
            await bot.send_message(
                chat_id=chat_id,
                text=chunk,
                parse_mode=ParseMode.HTML,
                disable_web_page_preview=True,
            )
        except BadRequest as exc:
            logger.warning("Не удалось отправить сообщение с HTML-разметкой (%s), отправляю как обычный текст", exc)
            await bot.send_message(
                chat_id=chat_id,
                text=_strip_html(chunk),
                disable_web_page_preview=True,
            )
