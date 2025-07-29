from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse
from django.views.decorators.http import require_http_methods
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Collect, Payment
from .pagination import Pagination
from .permissions import AuthorOrReadOnly, DonorOrReadOnly, IsDonatorOfCollect
from .serializers import (
    CollectSerializer, PaymentSerializer, RegisterSerializer,
    PaymentCommentSerializer, PaymentLikeSerializer
)
from .tasks import send_donation_emails, send_collect_creation_email


class CollectViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с сборами. Поддерживает CRUD-операции для сборов,
    а также кэширование данных для ускорения работы с часто запрашиваемыми коллекциями.
    """
    queryset = Collect.objects.select_related('author').prefetch_related('payments')
    serializer_class = CollectSerializer
    permission_classes = [AuthorOrReadOnly]
    pagination_class = Pagination

    def get_cache_key(self, request, pk=None):
        """
        Генерирует уникальный ключ кэша для каждого запроса.

        Аргументы:
            request (Request): Запрос, содержащий параметры страницы и лимита.

        Возвращает:
            str: Уникальный ключ кэша.
        """
        page = request.query_params.get('page', 1)
        limit = request.query_params.get('limit', 10)
        return f"collects_page_{page}_limit_{limit}"

    def list(self, request, *args, **kwargs):
        """
        Возвращает список всех сборов, с возможностью использования кэша.

        Если данные есть в кэше, они возвращаются из кэша. Если данных нет, выполняется запрос
        к базе данных и результат кэшируется на 1 час.

        Аргументы:
            request (Request): Запрос на получение списка сборов.

        Возвращает:
            Response: Ответ с данными о сборах.
        """
        cache_key = self.get_cache_key(request)
        cached_data = cache.get(cache_key)
        if cached_data:
            return Response(cached_data)

        # Если данные нет в кэше, выполняем запрос
        response = super().list(request, *args, **kwargs)
        cache.set(cache_key, response.data, timeout=3600)  # Кэшируем данные на 1 час
        return response

    def perform_create(self, serializer):
        collect = serializer.save(author=self.request.user)

        # Отправляем email автору о создании сбора
        send_collect_creation_email.apply_async(
            args=[collect.author.email, collect.title],
            queue='emails'
        )
        send_collect_creation_email.delay(collect.author.email, collect.title)

        # Инвалидация кэша
        cache.delete(f"collects_page_1_limit_10")

        return collect

    @action(detail=True, methods=['get'], permission_classes=[AllowAny],
            url_path='get-link')
    def get_link(self, request, pk=None):
        """
        Возвращает существующую короткую
        ссылку для сбора или генерирует новую.
        """
        collect = self.get_object()  # Получаем сбор по pk
        if not collect.short_link:
            collect.short_link = collect.generate_unique_short_url()
            collect.save()
        # Формируем короткую ссылку
        short_url = (
            f"{self.request.scheme}://{self.request.get_host()}"
            f"/r/{collect.short_link}"
        )

        return Response({"short-link": short_url}, status=status.HTTP_200_OK)


class PaymentViewSet(viewsets.ModelViewSet):
    """
    ViewSet для работы с платежами. Поддерживает CRUD-операции для платежей,
    привязанных к конкретному сбору.
    """
    serializer_class = PaymentSerializer
    permission_classes = [DonorOrReadOnly]

    def get_collect(self):
        """
        Получает объект сбора (Collect), привязанный к текущему платежу.

        Возвращает:
            Collect: Объект сбора, к которому привязан платеж.

        Исключения:
            Http404: Если сбор не найден.
        """
        if getattr(self, 'swagger_fake_view', False):
            return None
        return get_object_or_404(Collect, id=self.kwargs.get('collect_id'))

    def get_queryset(self):
        """
        Возвращает все платежи, привязанные к конкретному сбору.

        Возвращает:
            QuerySet: Список платежей для конкретного сбора.
        """
        collect = self.get_collect()
        if collect is None:
            return Collect.objects.none()
        return collect.payments.all()

    def perform_create(self, serializer):
        """
        Создает новый платеж, ассоциируя его с текущим пользователем и сбором.

        Аргументы:
            serializer (PaymentSerializer): Сериализатор для создания нового платежа.

        Также:
            - Инвалидация кэша для страницы с платежами.
            - Обновление суммы сбора и количества доноров.
        """
        donor = self.request.user
        collect = self.get_collect()
        payment = serializer.save(collect=collect, donor=donor)

        # Инвалидация кэша
        cache.delete(f"collects_page_1_limit_10")

        collect.collected_amount += payment.amount
        collect.donors_count += 1
        collect.save()
        send_donation_emails.delay(donor.email, collect.author.email, payment.amount, collect.title)


class CommentsLikesBaseViewSet(viewsets.ModelViewSet):
    """
    Базовый ViewSet для комментариев и лайков
    """
    permission_classes = [permissions.IsAuthenticated, IsDonatorOfCollect]

    def get_payment(self):
        """
        Получаем платеж по ID из URL параметров.
        Если вызвано из Swagger — возвращаем None.
        """
        if getattr(self, 'swagger_fake_view', False):
            return None  # Swagger лезет сюда — просто игнорируем

        payment_id = self.kwargs.get('payment_id')
        if not payment_id:
            return None
        return get_object_or_404(Payment, id=payment_id)

    def perform_create(self, serializer):
        """
        Этот метод будет использоваться для сохранения данных, связанных с платежом.
        """
        serializer.save(payment=self.get_payment(), user=self.request.user)

    def get_queryset(self):
        """
        Базовая заглушка — должна быть переопределена.
        """
        raise NotImplementedError("get_queryset() должен быть переопределен в дочернем классе.")


class PaymentLikeViewSet(CommentsLikesBaseViewSet):
    """
    ViewSet для управления лайками платежей.
    Позволяет получать список лайков, ассоциированных с конкретным платежом.
    """
    serializer_class = PaymentLikeSerializer

    def get_queryset(self):
        """
        Получаем все лайки, связанные с конкретным платежом.

        Возвращает:
            QuerySet: Список лайков, ассоциированных с платежом.
        """
        payment = self.get_payment()
        if not payment:
            return None
        return payment.likes.all()


class PaymentCommentViewSet(CommentsLikesBaseViewSet):
    """
    ViewSet для управления комментариями на платежах.
    Позволяет получать список комментариев, ассоциированных с конкретным платежом.
    """
    serializer_class = PaymentCommentSerializer

    def get_queryset(self):
        """
        Получаем все комментарии, связанные с конкретным платежом.

        Возвращает:
            QuerySet: Список комментариев, ассоциированных с платежом.
        """
        payment = self.get_payment()
        if not payment:
            return None
        return payment.comments.all()



class RegisterView(APIView):
    """
    View для регистрации нового пользователя.
    """
    def post(self, request):
        """
        Регистрирует нового пользователя, принимая данные из запроса.

        Аргументы:
            request (Request): Данные пользователя для регистрации.

        Возвращает:
            Response: Ответ с результатом регистрации (успех или ошибка).
        """
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Пользователь создан."}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@require_http_methods(["GET"])
def redirect_short_link(request, short_link):
    """
    Обрабатывает переход по короткой ссылке и переадресовывает
    на оригинальный сбор.
    """
    # Ищем сбор по короткой ссылке
    collect = get_object_or_404(Collect, short_link=short_link)
    # Переадресовываем на оригинальный URL сбора
    return redirect(reverse('collect-detail', kwargs={'pk': collect.id}))
