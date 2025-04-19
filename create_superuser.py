import os
from django.contrib.auth import get_user_model

# Установим настройки Django
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
import django
django.setup()

# Получаем модель пользователя
User = get_user_model()

# Проверяем, если суперпользователь уже существует, то не создаем его
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@example.com', 'admin')
    print("✅ Суперпользователь создан.")
else:
    print("✅ Суперпользователь уже существует.")
