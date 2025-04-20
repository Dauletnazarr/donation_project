import traceback

from celery import shared_task
from django.conf import settings
from django.core.mail import send_mail
import os
print("📦 DJANGO_SETTINGS_MODULE =", os.getenv("DJANGO_SETTINGS_MODULE"))


@shared_task
def send_donation_emails(donor_email, author_email, amount, collect_title=None):
    """
    Отправляет письма донору и автору сбора.

    Письмо донору: подтверждение о донате.
    Письмо автору: уведомление о новом донате.

    Аргументы:
        donor_email (str): Email донора.
        author_email (str): Email автора сбора.
        amount (Decimal): Сумма доната.
        collect_title (str): Название сбора, если нужно отправить письмо об его создании.
    """
    print("📨 Старт отправки письма...")

    try:
        # Письмо донору
        send_mail(
            subject='Спасибо за донат!',
            message=f'Вы отправили {amount} ₽ на сбор "{collect_title}".',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[donor_email],
            fail_silently=False,
        )

        # Письмо автору
        send_mail(
            subject=f'Новый донат для сбора "{collect_title}"',
            message=f'Вы получили донат на сумму {amount} ₽.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[author_email],
            fail_silently=False,
        )

        print("📬 Письма отправлены.")

    except Exception as e:
        print("❌ Ошибка при отправке писем:")
        print(traceback.format_exc())
