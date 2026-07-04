import asyncio
import json
import logging
import re
from typing import Any, List, Dict

from telegram import Update
from telegram.ext import ContextTypes

from modules.auth import restricted
from modules.gemini_client import ask_gemini
from modules.prompts import MEMORY_UPDATE_PROMPT, TRAIN_PARSE_PROMPT, TRAIN_ANALYSIS_PROMPT
from modules.telegram_utils import safe_send
from modules import db

logger = logging.getLogger(__name__)

# --- Вспомогательные утилиты парсинга ---

def _extract_json_from_text(text: str) -> str:
    """
    Агрессивно очищает ответ модели от markdown-мусора.
    Ищет первую вложенную структуру JSON (список или объект).
    """
    text = text.strip()
    # Ищем границы JSON: [...] или {...}
    match = re.search(r'(\[[\s\S]*\]|\{[\s\S]*\})', text)
    if match:
        return match.group(1)
    return text

def _parse_llm_response(text: str) -> Any:
    """Обертка над json.loads с очисткой."""
    cleaned = _extract_json_from_text(text)
    return json.loads(cleaned)

# --- Валидация схем данных ---

def _validate_memory(data: Any) -> List[str]:
    if not isinstance(data, list):
        raise ValueError("Память должна быть списком строк.")
    return [str(item).strip() for item in data if str(item).strip()]

def _validate_workout(data: Any) -> List[Dict[str, Any]]:
    if not isinstance(data, list):
        raise ValueError("Данные тренировки должны быть списком.")
    
    validated = []
    for entry in data:
        if not isinstance(entry, dict) or "exercise" not in entry:
            continue
        validated.append({
            "exercise": str(entry.get("exercise", "Unknown")),
            "sets": entry.get("sets", []),
            "general_feeling": str(entry.get("general_feeling", ""))
        })
    return validated

# --- Хендлеры ---

@restricted
async def remember_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    
    # Режим чтения
    if not context.args:
        memory = await asyncio.to_thread(db.get_memory)
        if not memory:
            await safe_send(context.bot, chat_id, "🧠 Память пуста.")
            return
        msg = "🧠 Мои знания о тебе:\n" + "\n".join(f"• {f}" for f in memory)
        await safe_send(context.bot, chat_id, msg)
        return

    # Режим записи
    raw_input = " ".join(context.args)
    current_memory = await asyncio.to_thread(db.get_memory)
    
    prompt = f"Текущие факты: {json.dumps(current_memory)}\n\nНовый факт: {raw_input}"
    
    try:
        response = await ask_gemini(MEMORY_UPDATE_PROMPT, prompt)
        parsed = _parse_llm_response(response)
        validated = _validate_memory(parsed)
        
        await asyncio.to_thread(db.save_memory, validated)
        await safe_send(context.bot, chat_id, "✅ Память обновлена.")
    except Exception as e:
        logger.error(f"Error in remember: {e}")
        await safe_send(context.bot, chat_id, "❌ Ошибка при обновлении памяти.")

@restricted
async def train_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    if not context.args:
        await safe_send(context.bot, chat_id, "🏋️‍♂️ Используй: /train [описание тренировки]")
        return

    raw_text = " ".join(context.args)
    try:
        response = await ask_gemini(TRAIN_PARSE_PROMPT, raw_text)
        parsed = _parse_llm_response(response)
        validated = _validate_workout(parsed)
        
        await asyncio.to_thread(db.save_workout, raw_text, json.dumps(validated, ensure_ascii=False))
        await safe_send(context.bot, chat_id, "✅ Тренировка сохранена.")
    except Exception as e:
        logger.error(f"Error in train: {e}")
        await safe_send(context.bot, chat_id, "❌ Ошибка парсинга тренировки.")

@restricted
async def traininfo_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    
    workouts = await asyncio.to_thread(db.get_recent_workouts, 15)
    if not workouts:
        await safe_send(context.bot, chat_id, "📉 Нет данных для анализа.")
        return

    try:
        analysis = await ask_gemini(TRAIN_ANALYSIS_PROMPT, json.dumps(workouts, ensure_ascii=False))
        await safe_send(context.bot, chat_id, f"📈 Аналитика:\n\n{analysis}")
    except Exception as e:
        logger.error(f"Error in traininfo: {e}")
        await safe_send(context.bot, chat_id, "❌ Ошибка при анализе.")
