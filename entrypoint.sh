#!/bin/bash
set -e

# Запуск только если это web
if [ "$RUN_MAIN" != "true" ]; then
  echo "🔄 Применяем миграции..."
  poetry run python manage.py makemigrations
  poetry run python manage.py migrate

  echo "📦 Загружаем мок-данные..."
  poetry run python run_mock_data.py

  echo "👤 Создание суперпользователя..."
  poetry run python manage.py shell << END
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')
    print("✅ Суперпользователь создан.")
else:
    print("✅ Суперпользователь уже существует.")
END
fi

# 🚀 Запускаем сервер
echo "🚀 Запускаем Django сервер..."
exec poetry run python manage.py runserver 0.0.0.0:8000
