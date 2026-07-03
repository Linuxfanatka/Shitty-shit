"""
handlers/news.py

Логика новостного дайджеста:
  сбор всех RSS-лент -> отбор ещё не показанных новостей ->
  анализ и сравнение источников через Gemini -> отправка пользователю.

Функция send_news_digest переиспользуется и командой /news, и
планировщиком автоматических ежедневных дайджестов (modules/scheduler.py).
"""

import logging

from telegram import Bot, Update
from telegram.ext import ContextTypes

from modules.auth import restricted
from modules.gemini_client import ask_gemini
from modules.prompts import NEWS_SYSTEM_PROMPT
from modules.rss_parser import collect_all_news
from modules.storage import filter_unseen, mark_seen
from modules.telegram_utils import safe_send

logger = logging.getLogger(__name__)


def _format_news_for_model(entries: list[dict]) -> str:
    """Готовит новости в виде текстового блока, понятного и удобного для модели."""
    blocks = []
    for e in entries:
        blocks.append(
            "Источник: {source}\n"
            "Заголовок: {title}\n"
            "Описание: {summary}\n"
            "Ссылка: {link}".format(**e)
        )
    return "\n\n---\n\n".join(blocks)


async def send_news_digest(bot: Bot, chat_id: int, only_new: bool = True) -> None:
    """
    Собирает новости со всех настроенных лент, при необходимости
    отфильтровывает уже показанные ранее, отправляет их на анализ в
    Gemini и присылает готовый дайджест пользователю.
    """
    all_entries = await collect_all_news()
    if not all_entries:
        await bot.send_message(chat_id=chat_id, text="Свежих новостей по настроенным RSS-лентам не нашлось.")
        return

    entries = filter_unseen(all_entries) if only_new else all_entries
    if not entries:
        await bot.send_message(chat_id=chat_id, text="Новых новостей с последнего дайджеста нет.")
        return

    await bot.send_message(chat_id=chat_id, text=f"Анализирую {len(entries)} новостей…")

    model_input = _format_news_for_model(entries)
    try:
        digest_text = await ask_gemini(NEWS_SYSTEM_PROMPT, model_input)
    except Exception:
        logger.exception("Не удалось получить дайджест от Gemini")
        await bot.send_message(
            chat_id=chat_id,
            text="Не получилось построить дайджест — сбой при обращении к нейросети. Попробуй ещё раз чуть позже.",
        )
        return

    await safe_send(bot, chat_id, digest_text)
    # Помечаем как показанные только после успешной отправки, чтобы при
    # сбое новости не "потерялись" и попали в следующую попытку.
    mark_seen(entries)


@restricted
async def news_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_news_digest(context.bot, update.effective_chat.id, only_new=True)
