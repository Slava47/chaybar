FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Создаём пользователя заранее (без root-доступа)
RUN useradd -m -u 1000 botuser
USER botuser

# Копируем файлы от пользователя (без смены владельца)
COPY --chown=botuser:botuser bot.py .
COPY --chown=botuser:botuser tea_photos/ ./tea_photos/

# Устанавливаем зависимости
RUN pip install --no-cache-dir pyTelegramBotAPI==4.16.1

# Запуск
CMD ["python", "bot.py"]
