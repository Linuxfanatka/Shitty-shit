"""
modules/gemini_client.py

Тонкая асинхронная обёртка над официальным Google GenAI SDK (пакет
google-genai, `from google import genai`) для вызова модели Gemini.

Ключ API берётся из переменной окружения GEMINI_API_KEY (см. config.py),
модель — тоже настраивается через переменную окружения GEMINI_MODEL
(по умолчанию gemini-3.5-flash).

Все системные промпты вынесены в modules/prompts.py — здесь только
механика обращения к API.
"""

import logging

from google import genai
from google.genai import types

from config import GEMINI_API_KEY, GEMINI_MODEL

logger = logging.getLogger(__name__)

# Клиент создаётся один раз при импорте модуля и переиспользуется
# во всех обращениях к Gemini за время жизни процесса бота.
_client = genai.Client(api_key=GEMINI_API_KEY)


async def ask_gemini(system_prompt: str, user_content: str, temperature: float = 0.4) -> str:
    """
    Отправляет запрос в Gemini и возвращает текст ответа.

    В случае ошибки (сеть, квота, некорректный ответ) исключение
    пробрасывается выше — вызывающий код (handlers/*) сам решает,
    что показать пользователю в чате.
    """
    try:
        response = await _client.aio.models.generate_content(
            model=GEMINI_MODEL,
            contents=user_content,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                temperature=temperature,
                max_output_tokens=2048,
            ),
        )
    except Exception:
        logger.exception("Ошибка при обращении к Gemini API")
        raise

    text = (response.text or "").strip()
    if not text:
        raise RuntimeError("Gemini вернул пустой ответ")
    return text
