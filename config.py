"""
config.py

Единая точка загрузки конфигурации бота из переменных окружения (.env).

Важные архитектурные решения:
- Список RSS-лент хранится как 10 ОТДЕЛЬНЫХ переменных RSS_FEED_1..RSS_FEED_10,
  а не как список в коде или один общий параметр. Это сделано специально по
  требованию: реальные адреса источников новостей существуют только в .env
  на твоём сервере и никогда не попадают в код/репозиторий.
- Ключи (Telegram, Gemini) и координаты для погоды — тоже только в .env.
- Если какая-то обязательная переменная не задана, процесс сразу
  останавливается с понятным сообщением, а не падает в рантайме в
  неожиданный момент посреди работы.
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()


def _require(name: str) -> str:
    value = os.getenv(name)
    if not value:
        sys.exit(
            f"Переменная окружения {name} не задана. "
            f"Скопируй .env.example в .env и заполни его перед запуском бота."
        )
    return value


def _get_int(name: str, default: int) -> int:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    try:
        return int(raw)
    except ValueError:
        sys.exit(f"Переменная окружения {name} должна быть целым числом, получено: {raw!r}")


def _get_bool(name: str, default: bool) -> bool:
    raw = os.getenv(name)
    if raw is None or raw.strip() == "":
        return default
    return raw.strip().lower() in ("1", "true", "yes", "on", "да")


# ====================== Telegram ======================

TELEGRAM_BOT_TOKEN = _require("TELEGRAM_BOT_TOKEN")

TELEGRAM_ALLOWED_USER_ID = _get_int("TELEGRAM_ALLOWED_USER_ID", 0)
if TELEGRAM_ALLOWED_USER_ID == 0:
    sys.exit(
        "Переменная окружения TELEGRAM_ALLOWED_USER_ID не задана. "
        "Узнать свой Telegram ID можно, например, у бота @userinfobot."
    )

# ====================== Gemini (Google GenAI) ======================

GEMINI_API_KEY = _require("GEMINI_API_KEY")
GEMINI_MODEL = os.getenv("GEMINI_MODEL", "gemini-3.5-flash")

# ====================== RSS-ленты ======================
# Намеренно 10 отдельных переменных вместо одного списка — см. пояснение
# в шапке файла.

RSS_FEEDS = [
    url
    for url in (
        os.getenv("RSS_FEED_1"),
        os.getenv("RSS_FEED_2"),
        os.getenv("RSS_FEED_3"),
        os.getenv("RSS_FEED_4"),
        os.getenv("RSS_FEED_5"),
        os.getenv("RSS_FEED_6"),
        os.getenv("RSS_FEED_7"),
        os.getenv("RSS_FEED_8"),
        os.getenv("RSS_FEED_9"),
        os.getenv("RSS_FEED_10"),
    )
    if url and url.strip()
]

MAX_ITEMS_PER_FEED = _get_int("MAX_ITEMS_PER_FEED", 5)
NEWS_LOOKBACK_HOURS = _get_int("NEWS_LOOKBACK_HOURS", 24)
SEEN_NEWS_RETENTION_DAYS = _get_int("SEEN_NEWS_RETENTION_DAYS", 14)

# ====================== Погода (Open-Meteo, API-ключ не требуется) ======================

WEATHER_LATITUDE = os.getenv("WEATHER_LATITUDE", "56.0184")
WEATHER_LONGITUDE = os.getenv("WEATHER_LONGITUDE", "92.8672")

# ====================== Расписание автоматических рассылок ======================

TIMEZONE = os.getenv("TIMEZONE", "UTC")
DIGEST_TIME = os.getenv("DIGEST_TIME", "08:00")
WEATHER_TIME = os.getenv("WEATHER_TIME", "07:30")
AUTO_NEWS_ENABLED = _get_bool("AUTO_NEWS_ENABLED", True)
AUTO_WEATHER_ENABLED = _get_bool("AUTO_WEATHER_ENABLED", True)

# ====================== Логирование ======================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO").upper()
