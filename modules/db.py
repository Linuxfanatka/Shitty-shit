import sqlite3
import json
import os
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

# Путь к БД в папке data/
DATA_DIR = Path("data")
DB_PATH = DATA_DIR / "bot_database.db"

def _get_connection():
    """Создает соединение и гарантирует, что все таблицы существуют."""
    DATA_DIR.mkdir(exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    
    # Инициализация всех таблиц, если они не существуют
    conn.execute('''
        CREATE TABLE IF NOT EXISTS user_memory (
            id INTEGER PRIMARY KEY CHECK (id = 1),
            facts_json TEXT
        )
    ''')
    conn.execute('''
        CREATE TABLE IF NOT EXISTS workouts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            raw_text TEXT,
            data_json TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    return conn

def get_memory():
    """Получает список фактов из БД."""
    conn = _get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT facts_json FROM user_memory WHERE id = 1')
        row = cursor.fetchone()
        return json.loads(row[0]) if row else []
    finally:
        conn.close()

def save_memory(facts: list):
    """Сохраняет список фактов в БД."""
    conn = _get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT OR REPLACE INTO user_memory (id, facts_json) VALUES (1, ?)',
            (json.dumps(facts, ensure_ascii=False),)
        )
        conn.commit()
    finally:
        conn.close()

def save_workout(raw_text, json_data):
    """Сохраняет новую тренировку."""
    conn = _get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute(
            'INSERT INTO workouts (raw_text, data_json) VALUES (?, ?)',
            (raw_text, json_data)
        )
        conn.commit()
    finally:
        conn.close()

def get_recent_workouts(limit=15):
    """Получает последние N тренировок."""
    conn = _get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute('SELECT data_json FROM workouts ORDER BY id DESC LIMIT ?', (limit,))
        rows = cursor.fetchall()
        return [json.loads(row[0]) for row in rows]
    finally:
        conn.close()
