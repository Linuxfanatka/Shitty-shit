"""
modules/weather.py

Получение текущей погоды и прогноза максимума/минимума температуры на
сегодня через бесплатный Open-Meteo API (регистрация и API-ключ не
требуются). Координаты берутся из .env (WEATHER_LATITUDE / WEATHER_LONGITUDE).
"""

import logging

import httpx

from config import WEATHER_LATITUDE, WEATHER_LONGITUDE

logger = logging.getLogger(__name__)

WEATHER_API_URL = "https://api.open-meteo.com/v1/forecast"


async def fetch_weather() -> dict:
    """
    Запрашивает текущую погоду и дневной прогноз для координат из .env.
    Возвращает "сырой" JSON-ответ Open-Meteo как словарь — его
    интерпретацией в человеческий текст-совет занимается уже Gemini.
    """
    params = {
        "latitude": WEATHER_LATITUDE,
        "longitude": WEATHER_LONGITUDE,
        "current": "temperature_2m,apparent_temperature,precipitation,wind_speed_10m",
        "daily": "temperature_2m_max,temperature_2m_min",
        "timezone": "auto",
    }

    async with httpx.AsyncClient(timeout=15) as client:
        response = await client.get(WEATHER_API_URL, params=params)
        response.raise_for_status()
        return response.json()


def build_weather_summary_text(data: dict) -> str:
    """
    Превращает сырой ответ Open-Meteo в компактный текстовый блок с
    единицами измерения — именно этот текст передаётся Gemini как
    входные данные для рекомендаций по одежде и предупреждений.
    """
    current = data.get("current", {}) or {}
    current_units = data.get("current_units", {}) or {}
    daily = data.get("daily", {}) or {}
    daily_units = data.get("daily_units", {}) or {}

    def unit(key: str, units: dict) -> str:
        return units.get(key, "")

    max_list = daily.get("temperature_2m_max") or [None]
    min_list = daily.get("temperature_2m_min") or [None]
    today_max = max_list[0]
    today_min = min_list[0]

    lines = [
        f"Текущая температура: {current.get('temperature_2m')}{unit('temperature_2m', current_units)}",
        f"Ощущается как: {current.get('apparent_temperature')}{unit('apparent_temperature', current_units)}",
        f"Осадки сейчас: {current.get('precipitation')} {unit('precipitation', current_units)}",
        f"Скорость ветра: {current.get('wind_speed_10m')} {unit('wind_speed_10m', current_units)}",
        f"Максимальная температура сегодня: {today_max}{unit('temperature_2m_max', daily_units)}",
        f"Минимальная температура сегодня: {today_min}{unit('temperature_2m_min', daily_units)}",
    ]
    return "\n".join(lines)
