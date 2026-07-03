FROM python:3.12-slim

WORKDIR /app

# Сначала только зависимости — так пересборка образа при изменении кода
# не будет каждый раз заново скачивать пакеты
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# data/ содержит историю показанных новостей — она должна переживать
# пересборку и перезапуск контейнера, монтируется как volume
VOLUME ["/app/data"]

CMD ["python", "bot.py"]
