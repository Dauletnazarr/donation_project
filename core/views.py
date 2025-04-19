from django.conf import settings
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
from .tasks import send_donation_emails


class CollectViewSet(viewsets.ModelViewSet):
    queryset = Collect.objects.select_related('author').prefetch_related('payments')
    serializer_class = CollectSerializer
    permission_classes = [AuthorOrReadOnly]
    pagination_class = Pagination

    def perform_create(self, serializer):
        collect = serializer.save(author=self.request.user)

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
    serializer_class = PaymentSerializer
    permission_classes = [DonorOrReadOnly]

    def get_collect(self):
        if getattr(self, 'swagger_fake_view', False):
            return None
        return get_object_or_404(Collect, id=self.kwargs.get('collect_id'))

    def get_queryset(self):
        """
        Возвращаем платежи, привязанные к конкретному сбору.
        """
        collect = self.get_collect()
        if collect is None:
            return Collect.objects.none()  # или просто []
        return collect.payments.all()

    def perform_create(self, serializer):
        donor = self.request.user
        collect = self.get_collect()
        payment = serializer.save(collect=collect, donor=donor)

        collect.collected_amount += payment.amount
        collect.donors_count += 1
        collect.save()
        print('aaa')
        send_donation_emails.delay(donor.email, collect.author.email, payment.amount)


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
    serializer_class = PaymentLikeSerializer

    def get_queryset(self):
        payment = self.get_payment()
        if not payment:
            return None
        return payment.likes.all()


class PaymentCommentViewSet(CommentsLikesBaseViewSet):
    serializer_class = PaymentCommentSerializer

    def get_queryset(self):
        payment = self.get_payment()
        if not payment:
            return None
        return payment.comments.all()


class RegisterView(APIView):
    def post(self, request):
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
