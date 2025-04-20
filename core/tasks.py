import traceback
from email.header import Header

from celery import shared_task
from django.conf import settings
from django.core.mail import EmailMessage
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
        EmailMessage(
            subject=str(Header('Спасибо за донат!', 'utf-8')),
            body=f'Вы отправили {amount} ₽.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[donor_email],
        ).send(fail_silently=False)

        # Письмо автору
        EmailMessage(
            subject=str(Header('Новый донат на ваш сбор', 'utf-8')),
            body=f'Вы получили донат на сумму {amount} ₽.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[author_email],
        ).send(fail_silently=False)

    except Exception:
        print("❌ Ошибка при отправке писем:")
        print(traceback.format_exc())


@shared_task
def send_collect_creation_email(author_email, collect_title):
    """
    Отправляет письмо автору сбора с уведомлением о том, что сбор был успешно создан.

    Аргументы:
        author_email (str): Email автора сбора.
        collect_title (str): Название сбора.
    """
    print("📨 Старт отправки письма о создании сбора...")

    try:
        EmailMessage(
            subject=str(Header('Сбор успешно создан', 'utf-8')),
            body=f'Ваш сбор «{collect_title}» был успешно создан.',
            from_email=settings.DEFAULT_FROM_EMAIL,
            to=[author_email],
        ).send(fail_silently=False)

    except Exception:
        print("❌ Ошибка при отправке письма:")
        print(traceback.format_exc())

