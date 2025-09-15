# Базовый образ Python 3.10
FROM python:3.10-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем requirements.txt и устанавливаем библиотеки
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем все файлы проекта
COPY . .

# Запускаем бот
CMD ["python", "bot.py"]