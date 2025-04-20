# config/celery.py
import os
from celery import Celery

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings')

app = Celery('config')
app.config_from_object('django.conf:settings', namespace='CELERY')
app.autodiscover_tasks()

app.conf.task_routes = {
    'core.tasks.send_donation_emails': {'queue': 'emails'},
    'core.tasks.send_collect_creation_email': {'queue': 'emails'},
}
