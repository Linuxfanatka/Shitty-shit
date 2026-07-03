"""
handlers/ask.py

Дополнительная команда /ask <вопрос> — свободное общение с Gemini прямо
в боте, чтобы это был не только новостной/погодный инструмент, а
действительно личный AI-ассистент. Диалог без памяти (каждый вопрос
обрабатывается независимо) — этого достаточно для быстрых вопросов.
"""

import logging

from telegram import Update
from telegram.ext import ContextTypes

from modules.auth import restricted
from modules.gemini_client import ask_gemini
from modules.prompts import ASK_SYSTEM_PROMPT
from modules.telegram_utils import safe_send

logger = logging.getLogger(__name__)


@restricted
async def ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    question = " ".join(context.args) if context.args else ""
    if not question:
        await update.message.reply_text(
            "Напиши вопрос после команды, например:\n/ask объясни разницу между TCP и UDP"
        )
        return

    await update.message.chat.send_action("typing")
    try:
        answer = await ask_gemini(ASK_SYSTEM_PROMPT, question)
    except Exception:
        logger.exception("Не удалось получить ответ от Gemini")
        await update.message.reply_text("Не получилось получить ответ — сбой при обращении к нейросети.")
        return

    await safe_send(context.bot, update.effective_chat.id, answer)
