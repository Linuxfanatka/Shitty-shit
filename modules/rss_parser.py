"""
modules/rss_parser.py

Загрузка и первичная обработка RSS/Atom-лент. Список лент задаётся через
переменные окружения RSS_FEED_1 ... RSS_FEED_10 (см. config.py) — это
сделано специально, чтобы реальные адреса источников не попадали в код
и в git-репозиторий, а хранились только в .env на твоём сервере.

feedparser.parse() — блокирующая операция (сеть + разбор XML), поэтому
каждая лента обрабатывается в отдельном потоке через asyncio.to_thread,
а все ленты опрашиваются параллельно.
"""

import asyncio
import logging
import time
from email.utils import mktime_tz, parsedate_tz

import feedparser

from config import MAX_ITEMS_PER_FEED, NEWS_LOOKBACK_HOURS, RSS_FEEDS

logger = logging.getLogger(__name__)

feedparser.USER_AGENT = "PersonalAIAssistantBot/1.0"


def _entry_timestamp(entry) -> float | None:
    """Пытается достать время публикации записи в unix-времени."""
    for key in ("published_parsed", "updated_parsed"):
        value = getattr(entry, key, None)
        if value:
            return time.mktime(value)

    # некоторые ленты отдают дату только строкой без разбора feedparser'ом
    raw = getattr(entry, "published", None) or getattr(entry, "updated", None)
    if raw:
        parsed = parsedate_tz(raw)
        if parsed:
            return mktime_tz(parsed)

    return None


def _parse_one_feed(url: str) -> list[dict]:
    """Синхронная загрузка и разбор одной ленты (выполняется в отдельном потоке)."""
    parsed = feedparser.parse(url)

    if parsed.bozo and not parsed.entries:
        logger.warning("Не удалось разобрать ленту %s: %s", url, parsed.get("bozo_exception"))
        return []

    source_title = parsed.feed.get("title", url)
    cutoff = time.time() - NEWS_LOOKBACK_HOURS * 3600

    items: list[dict] = []
    # берём с запасом до фильтрации по времени, чтобы после отсева старых
    # записей всё равно осталось нужное количество свежих
    for entry in parsed.entries[: MAX_ITEMS_PER_FEED * 3]:
        link = entry.get("link")
        title = entry.get("title")
        if not link or not title:
            continue

        published_ts = _entry_timestamp(entry)
        if published_ts is not None and published_ts < cutoff:
            continue

        summary = (entry.get("summary") or entry.get("description") or "").strip()
        if len(summary) > 600:
            summary = summary[:600].rsplit(" ", 1)[0] + "…"

        items.append(
            {
                "source": source_title,
                "title": title.strip(),
                "summary": summary,
                "link": link,
                "published_ts": published_ts or time.time(),
            }
        )
        if len(items) >= MAX_ITEMS_PER_FEED:
            break

    return items


async def collect_all_news() -> list[dict]:
    """
    Асинхронно опрашивает все настроенные RSS-ленты параллельно и
    возвращает объединённый список новостей, отсортированный от новых
    к старым. Ошибка в одной ленте не мешает обработать остальные.
    """
    if not RSS_FEEDS:
        logger.warning("Не задано ни одной RSS-ленты (RSS_FEED_1..RSS_FEED_10 пусты в .env)")
        return []

    tasks = [asyncio.to_thread(_parse_one_feed, url) for url in RSS_FEEDS]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_items: list[dict] = []
    for url, result in zip(RSS_FEEDS, results):
        if isinstance(result, Exception):
            logger.error("Ошибка при обработке ленты %s: %s", url, result)
            continue
        all_items.extend(result)

    all_items.sort(key=lambda item: item["published_ts"], reverse=True)
    return all_items
