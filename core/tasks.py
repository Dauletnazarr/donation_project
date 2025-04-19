import traceback

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
import os
print("📦 DJANGO_SETTINGS_MODULE =", os.getenv("DJANGO_SETTINGS_MODULE"))


@shared_task
def send_donation_emails(donor_email, author_email, amount):
    print("📨 Старт отправки письма...")
    try:
        send_mail(
            subject='Спасибо за донат!',
            message=f'Вы отправили {amount} ₽.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[donor_email],
            fail_silently=False,
        )
        send_mail(
            subject='Новый донат',
            message=f'Вы получили донат на сумму {amount} ₽.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[author_email],
            fail_silently=False,
        )
        print("📬 Письма отправлены.")
    except Exception as e:
        print("❌ Ошибка при отправке писем:")
        print(traceback.format_exc())