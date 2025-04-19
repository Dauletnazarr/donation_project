# Используем официальный образ Python
FROM python:3.12-slim

# Устанавливаем зависимость для Poetry
RUN pip install --no-cache-dir poetry

# Устанавливаем рабочую директорию
WORKDIR /app

# Создаем папку для сохранения отправленных писем
RUN mkdir /app/sent_emails

# Копируем скрипт entrypoint внутрь контейнера
COPY entrypoint.sh /app/entrypoint.sh

# Делаем скрипт исполняемым (не обязательно на Windows, но желательно на Unix)
RUN chmod +x /app/entrypoint.sh

# Копируем файлы проекта в контейнер
COPY pyproject.toml poetry.lock /app/

# Устанавливаем зависимости через Poetry
RUN poetry install --no-root

# Копируем оставшиеся файлы
COPY . /app/

# Устанавливаем переменные окружения для базы данных
ENV POSTGRES_HOST=postgres
ENV POSTGRES_PORT=5432
ENV POSTGRES_DB=donation_db
ENV POSTGRES_USER=postgres
ENV POSTGRES_PASSWORD=admin

# Открываем порт
EXPOSE 8000

# Указываем entrypoint
ENTRYPOINT ["sh", "/app/entrypoint.sh"]

# Команда для запуска сервера Django
CMD ["poetry", "run", "python", "manage.py", "runserver", "0.0.0.0:8000"]
