"""
handlers/weather.py

Логика погодной сводки:
  запрос к Open-Meteo -> генерация совета по одежде и предупреждений
  через Gemini -> отправка пользователю.

Функция send_weather_report переиспользуется и командой /weather, и
планировщиком автоматических ежедневных сводок (modules/scheduler.py).
"""

import logging

from telegram import Bot, Update
from telegram.ext import ContextTypes

from modules.auth import restricted
from modules.gemini_client import ask_gemini
from modules.prompts import WEATHER_SYSTEM_PROMPT
from modules.telegram_utils import safe_send
from modules.weather import build_weather_summary_text, fetch_weather

logger = logging.getLogger(__name__)


async def send_weather_report(bot: Bot, chat_id: int) -> None:
    try:
        raw = await fetch_weather()
    except Exception:
        logger.exception("Не удалось получить данные от Open-Meteo")
        await bot.send_message(
            chat_id=chat_id,
            text="Не получилось получить данные о погоде. Попробуй ещё раз чуть позже.",
        )
        return

    summary = build_weather_summary_text(raw)

    try:
        advice = await ask_gemini(WEATHER_SYSTEM_PROMPT, summary)
    except Exception:
        logger.exception("Не удалось получить совет по одежде от Gemini")
        await bot.send_message(
            chat_id=chat_id,
            text="Погоду получил, но не смог сформировать совет — сбой нейросети.\n\n" + summary,
        )
        return

    await safe_send(bot, chat_id, advice)


@restricted
async def weather_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await send_weather_report(context.bot, update.effective_chat.id)
