import uuid

from django.db import models
from django.contrib.auth.models import User
from django.urls import reverse

from core.constants import SHORT_LINK_MAX_LENGTH


class Collect(models.Model):
    OCCASION_CHOICES = [
        ('birthday', 'День рождения'),
        ('wedding', 'Свадьба'),
        ('new_year', 'Новый год'),
        ('other', 'Другое'),
    ]

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='collections',
        verbose_name='Автор'
    )
    title = models.CharField(
        max_length=255,
        verbose_name='Название'
    )
    occasion = models.CharField(
        max_length=50,
        choices=OCCASION_CHOICES,
        verbose_name='Повод'
    )
    description = models.TextField(
        verbose_name='Описание'
    )
    goal_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name='Целевая сумма'
    )
    collected_amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        default=0,
        verbose_name='Собранная сумма'
    )
    donors_count = models.PositiveIntegerField(
        default=0,
        verbose_name='Количество доноров'
    )
    cover_image = models.ImageField(
        upload_to='covers/',
        null=True,
        blank=True,
        verbose_name='Обложка'
    )
    end_datetime = models.DateTimeField(
        verbose_name='Дата завершения сбора'
    )

    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата создания'
    )
    short_link = models.CharField(
        max_length=SHORT_LINK_MAX_LENGTH, verbose_name="Короткая ссылка",
        unique=True,
        null=True,
    )

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'сбор'
        verbose_name_plural = 'Сборы'
        ordering = ['-created_at']

    def generate_unique_short_url(self):
        """
        Генерация уникальной короткой ссылки.
        """
        while True:
            short_link = str(uuid.uuid4())[:8]  # Генерируем короткую ссылку
            if not Collect.objects.filter(short_link=short_link).exists():
                return short_link

    def get_absolute_url(self):
        # Возвращаем полный URL для отображения сбора
        return reverse('collect-detail', kwargs={'pk': self.pk})


class Payment(models.Model):
    collect = models.ForeignKey(
        Collect,
        on_delete=models.CASCADE,
        related_name='payments',
        verbose_name='Сбор'
    )
    donor = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Донор'
    )
    amount = models.DecimalField(
        max_digits=12,
        decimal_places=2,
        verbose_name='Сумма'
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name='Дата платежа'
    )

    def __str__(self):
        return f'{self.amount} by {self.donor}'

    class Meta:
        verbose_name = 'платеж'
        verbose_name_plural = 'Платежи'
        ordering = ['-created_at']


class PaymentInteractionBase(models.Model):
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ['-created_at']


class PaymentLike(PaymentInteractionBase):
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='likes')
    class Meta(PaymentInteractionBase.Meta):
        constraints = [
            models.UniqueConstraint(fields=['payment', 'user'], name='unique_like')
        ]
        verbose_name = 'лайк платежа'
        verbose_name_plural = 'Лайки на платежи'


class PaymentComment(PaymentInteractionBase):
    payment = models.ForeignKey(Payment, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()

    class Meta(PaymentInteractionBase.Meta):
        constraints = [
            models.UniqueConstraint(fields=['payment', 'user'], name='unique_comment')
        ]
        verbose_name = 'комментарий на платеж'
        verbose_name_plural = 'Комментарии на платежи'
