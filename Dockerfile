# Используем официальный образ Python
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем исходный код приложения
COPY bot.py .

# Создаем необходимые директории
RUN mkdir -p tea_photos

# Устанавливаем Python зависимости напрямую
RUN pip install --no-cache-dir pyTelegramBotAPI==4.16.1

RUN useradd -m -u 1000 botuser && chown -R botuser:botuser /app
USER botuser

# Команда запуска бота
CMD ["python", "bot.py"]
