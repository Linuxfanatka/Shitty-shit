"""
modules/storage.py

Простое персистентное хранилище "уже показанных" новостей, чтобы бот не
присылал один и тот же материал повторно в каждом дайджесте.

Хранится в JSON-файле data/seen_news.json в виде {ссылка: unix_timestamp}.
Для личного бота с одним пользователем полноценная БД ради одной таблицы
избыточна — обычного файла достаточно и его легко посмотреть/почистить руками.
"""

import json
import logging
import time
from pathlib import Path

from config import SEEN_NEWS_RETENTION_DAYS

logger = logging.getLogger(__name__)

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
SEEN_FILE = DATA_DIR / "seen_news.json"


def _ensure_data_dir() -> None:
    DATA_DIR.mkdir(parents=True, exist_ok=True)


def _load() -> dict:
    _ensure_data_dir()
    if not SEEN_FILE.exists():
        return {}
    try:
        with SEEN_FILE.open("r", encoding="utf-8") as fh:
            return json.load(fh)
    except (json.JSONDecodeError, OSError):
        logger.warning("Файл %s повреждён или недоступен, начинаю с чистого состояния", SEEN_FILE)
        return {}


def _save(data: dict) -> None:
    _ensure_data_dir()
    with SEEN_FILE.open("w", encoding="utf-8") as fh:
        json.dump(data, fh, ensure_ascii=False, indent=2)


def _prune(data: dict) -> dict:
    cutoff = time.time() - SEEN_NEWS_RETENTION_DAYS * 86400
    return {link: ts for link, ts in data.items() if ts >= cutoff}


def filter_unseen(entries: list[dict]) -> list[dict]:
    """Возвращает только те новости, ссылки которых ещё не встречались."""
    seen = _load()
    return [e for e in entries if e["link"] not in seen]


def mark_seen(entries: list[dict]) -> None:
    """Помечает новости как показанные и чистит устаревшие записи."""
    seen = _load()
    now = time.time()
    for e in entries:
        seen[e["link"]] = now
    seen = _prune(seen)
    _save(seen)
