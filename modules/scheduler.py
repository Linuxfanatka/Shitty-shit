"""
modules/scheduler.py

Настройка фоновых ежедневных задач (JobQueue) для автоматической отправки
новостного дайджеста и погодной сводки владельцу бота — без необходимости
вручную вызывать /news и /weather каждый раз.

Использует встроенный в python-telegram-bot APScheduler-based JobQueue
(требует установки extra: python-telegram-bot[job-queue], уже включено
в requirements.txt).
"""

import logging
from datetime import time as dt_time
from zoneinfo import ZoneInfo

from telegram.ext import Application, ContextTypes

from config import (
    AUTO_NEWS_ENABLED,
    AUTO_WEATHER_ENABLED,
    DIGEST_TIME,
    TELEGRAM_ALLOWED_USER_ID,
    TIMEZONE,
    WEATHER_TIME,
)
from handlers.news import send_news_digest
from handlers.weather import send_weather_report

logger = logging.getLogger(__name__)


def _parse_time(value: str, tz: ZoneInfo) -> dt_time:
    try:
        hour_str, minute_str = value.split(":")
        return dt_time(hour=int(hour_str), minute=int(minute_str), tzinfo=tz)
    except (ValueError, AttributeError) as exc:
        raise ValueError(
            f"Некорректный формат времени {value!r}, ожидается 'ЧЧ:ММ' (например, '08:00')"
        ) from exc


async def _scheduled_news(context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("Запускаю плановый новостной дайджест")
    await send_news_digest(context.bot, TELEGRAM_ALLOWED_USER_ID, only_new=True)


async def _scheduled_weather(context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("Запускаю плановую погодную сводку")
    await send_weather_report(context.bot, TELEGRAM_ALLOWED_USER_ID)


def setup_jobs(application: Application) -> None:
    """Регистрирует ежедневные задачи в JobQueue, если они включены в .env."""
    if application.job_queue is None:
        logger.warning(
            "JobQueue недоступен (не установлен extra 'job-queue' для "
            "python-telegram-bot) — автоматическая отправка по расписанию "
            "работать не будет, доступны только команды /news и /weather вручную."
        )
        return

    tz = ZoneInfo(TIMEZONE)

    if AUTO_NEWS_ENABLED:
        application.job_queue.run_daily(
            _scheduled_news,
            time=_parse_time(DIGEST_TIME, tz),
            name="daily_news_digest",
        )
        logger.info("Ежедневный новостной дайджест запланирован на %s (%s)", DIGEST_TIME, TIMEZONE)

    if AUTO_WEATHER_ENABLED:
        application.job_queue.run_daily(
            _scheduled_weather,
            time=_parse_time(WEATHER_TIME, tz),
            name="daily_weather_report",
        )
        logger.info("Ежедневная погодная сводка запланирована на %s (%s)", WEATHER_TIME, TIMEZONE)
