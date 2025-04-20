import uuid
from django.core.management.base import BaseCommand
from django.utils.timezone import now
from django.contrib.auth.models import User
from core.models import Collect, Payment, PaymentLike, PaymentComment
from django.db import transaction
from django.contrib.auth.hashers import make_password

class Command(BaseCommand):
    help = 'Генерирует пользователей, сборы, платежи, лайки и комментарии для тестов'

    def handle(self, *args, **options):
        num_users = 7
        num_collects_per_user = 10
        num_payments_per_collect = 20
        num_likes_per_payment = 3
        num_comments_per_payment = 2

        if Collect.objects.count() > 50:
            self.stdout.write(self.style.WARNING('✅ Моковые данные уже имеются. Пропускаем создание тестовых данных. '
                                                 'Или удалите все записи.'))
            return

        self.stdout.write(self.style.WARNING('Удаляем старые данные...'))
        PaymentLike.objects.all().delete()
        PaymentComment.objects.all().delete()
        Payment.objects.all().delete()
        Collect.objects.all().delete()
        User.objects.exclude(is_superuser=True).delete()

        self.stdout.write(self.style.WARNING('Создаём пользователей...'))
        users = []
        for i in range(num_users):
            users.append(User(
                username=f'user{i}',
                first_name=f'Имя{i}',
                last_name=f'Фамилия{i}',
                email=f'user{i}@test.com',
                password=make_password('password123')
            ))

        User.objects.bulk_create(users, batch_size=1000)
        users = list(User.objects.exclude(is_superuser=True))

        self.stdout.write(self.style.WARNING('Создаём сборы...'))
        collects = []
        short_links = set()
        for user in users:
            for j in range(num_collects_per_user):
                while True:
                    short_link = str(uuid.uuid4())[:8]
                    if short_link not in short_links:
                        short_links.add(short_link)
                        break
                collects.append(Collect(
                    author=user,
                    title=f'Сбор от {user.username} #{j}',
                    occasion='other',
                    description='Описание тестового сбора',
                    goal_amount=10000.00,
                    collected_amount=0,
                    donors_count=0,
                    end_datetime=now(),
                    created_at=now(),
                    short_link=short_link
                ))

        Collect.objects.bulk_create(collects, batch_size=1000)
        collects = list(Collect.objects.all())

        self.stdout.write(self.style.WARNING('Создаём платежи...'))
        payments = []
        for collect in collects:
            for k in range(num_payments_per_collect):
                donor = users[(hash(collect.title) + k) % len(users)]
                payments.append(Payment(
                    collect=collect,
                    donor=donor,
                    amount=100.00,
                    created_at=now()
                ))

        Payment.objects.bulk_create(payments, batch_size=1000)
        payments = list(Payment.objects.all())

        self.stdout.write(self.style.WARNING('Создаём лайки и комментарии...'))
        likes = []
        comments = []
        for payment in payments:
            for i in range(num_likes_per_payment):
                user = users[(hash(str(payment.id)) + i) % len(users)]
                likes.append(PaymentLike(
                    payment=payment,
                    user=user,
                    created_at=now()
                ))
            for j in range(num_comments_per_payment):
                user = users[(hash(str(payment.amount)) + j + 42) % len(users)]
                comments.append(PaymentComment(
                    payment=payment,
                    user=user,
                    text=f'Комментарий #{j} к платежу {payment.id}',
                    created_at=now()
                ))

        PaymentLike.objects.bulk_create(likes, batch_size=1000, ignore_conflicts=True)
        PaymentComment.objects.bulk_create(comments, batch_size=1000, ignore_conflicts=True)

        self.stdout.write(self.style.SUCCESS(f'✅ Готово!'))
        self.stdout.write(self.style.SUCCESS(f'Пользователи: {len(users)}'))
        self.stdout.write(self.style.SUCCESS(f'Сборы: {len(collects)}'))
        self.stdout.write(self.style.SUCCESS(f'Платежи: {len(payments)}'))
        self.stdout.write(self.style.SUCCESS(f'Лайки: {len(likes)}'))
        self.stdout.write(self.style.SUCCESS(f'Комментарии: {len(comments)}'))