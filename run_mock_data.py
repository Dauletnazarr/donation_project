import sys
import os

# Устанавливаем путь к проекту, чтобы Django мог найти настройки
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'  # Замените на имя вашего проекта

import django
django.setup()

from management.commands.generate_mock_data import Command

# Создаём экземпляр команды и вызываем её
command = Command()
command.handle()
