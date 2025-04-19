import random
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from core.models import Collect, Payment, PaymentLike, PaymentComment
from faker import Faker
from decimal import Decimal
from django.utils import timezone
from datetime import datetime

class Command(BaseCommand):
    help = 'Generates mock data for users, collections, payments, likes, and comments'

    def handle(self, *args, **kwargs):
        if Collect.objects.exists():
            self.stdout.write(self.style.WARNING('✅ Данные уже существуют. Генерация моков пропущена.'))
            return
        fake = Faker('ru_RU')

        # Генерация пользователей
        users = []
        for _ in range(100):
            user = User.objects.create_user(
                username=fake.user_name(),
                password=fake.password(),
                email=fake.email(),
                first_name=fake.first_name(),
                last_name=fake.last_name(),
            )
            users.append(user)

        # Генерация коллекций
        occasions = ['birthday', 'wedding', 'new_year', 'other']
        collections = []
        for _ in range(200):
            author = random.choice(users)
            end_date = fake.date_this_year()
            end_datetime = timezone.make_aware(datetime.combine(end_date, datetime.min.time()))
            collect = Collect.objects.create(
                author=author,
                title=fake.catch_phrase(),
                occasion=random.choice(occasions),
                description=fake.text(),
                goal_amount=Decimal(random.randint(1000, 50000)),
                collected_amount=Decimal(0),
                donors_count=0,
                cover_image=None,
                end_datetime=end_datetime,
            )
            collections.append(collect)

        # Генерация платежей
        payment_donors = {}  # collect пользователей, которые сделали платежи
        payments = []
        for _ in range(5000):
            collect = random.choice(collections)
            donor = random.choice(users)
            amount = Decimal(random.randint(10, 1000))
            created_at = timezone.make_aware(datetime.combine(fake.date_this_year(), datetime.min.time()))

            payment = Payment.objects.create(
                collect=collect,
                donor=donor,
                amount=amount,
                created_at=created_at,
            )
            payments.append(payment)

            collect.collected_amount += amount
            collect.donors_count += 1
            collect.save()

            # Сохраняем пользователя как донора
            if collect.id not in payment_donors:
                payment_donors[collect.id] = set()
            payment_donors[collect.id].add(donor.id)

        # Генерация лайков и комментариев
        for payment in random.sample(payments, k=300):  # Лайки только на некоторых платежах
            eligible_users = list(payment_donors.get(payment.collect.id, []))
            eligible_users = [u for u in eligible_users if u != payment.donor_id]
            random.shuffle(eligible_users)
            like_count = random.randint(3, min(10, len(eligible_users)))
            for user_id in eligible_users[:like_count]:
                try:
                    PaymentLike.objects.create(payment=payment, user=User.objects.get(id=user_id))
                except:
                    continue

            if random.choice([True, False]):
                comment_users = eligible_users[like_count:like_count+random.randint(1, 3)]
                for user_id in comment_users:
                    try:
                        PaymentComment.objects.create(
                            payment=payment,
                            user=User.objects.get(id=user_id),
                            text=fake.sentence(),
                        )
                    except:
                        continue

        self.stdout.write(self.style.SUCCESS('✅ Моковые данные созданы успешно'))
