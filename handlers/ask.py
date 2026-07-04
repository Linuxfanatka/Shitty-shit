import asyncio
from telegram import Update
from telegram.ext import ContextTypes

from modules.auth import restricted
from modules.gemini_client import ask_gemini
from modules.prompts import ASK_SYSTEM_PROMPT
from modules.telegram_utils import safe_send
from modules import db

@restricted
async def ask_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not context.args:
        await safe_send(context.bot, update.effective_chat.id, "Напиши свой вопрос после команды <code>/ask</code>.")
        return

    user_query = " ".join(context.args)
    
    # Достаем память из БД асинхронно
    memory_facts = await asyncio.to_thread(db.get_memory)
    
    # Динамически собираем системный промпт
    dynamic_prompt = ASK_SYSTEM_PROMPT
    if memory_facts:
        facts_str = "\n".join(f"- {fact}" for fact in memory_facts)
        dynamic_prompt += f"\n\nВАЖНЫЙ КОНТЕКСТ О ПОЛЬЗОВАТЕЛЕ:\n{facts_str}\nУчитывай эти данные при формировании ответа, если это релевантно вопросу."

    try:
        answer = await ask_gemini(dynamic_prompt, user_query)
        await safe_send(context.bot, update.effective_chat.id, answer)
    except Exception as e:
        # Логирование уже есть в gemini_client
        await safe_send(context.bot, update.effective_chat.id, "<i>Произошла ошибка при обращении к нейросети.</i>")
