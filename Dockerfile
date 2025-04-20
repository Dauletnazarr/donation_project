# Используем официальный образ Python
FROM python:3.12-slim

# Устанавливаем зависимость для Poetry
RUN pip install --no-cache-dir poetry

# Установим Celery
RUN pip install celery


# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем файлы проекта в контейнер
COPY pyproject.toml poetry.lock /app/

# Устанавливаем зависимости через Poetry
RUN poetry install --no-root

# Копируем оставшиеся файлы
COPY . /app/

# Открываем порт
EXPOSE 8000

# Команда для запуска сервера Django
CMD ["poetry", "run", "python", "manage.py", "runserver", "0.0.0.0:8000"]
