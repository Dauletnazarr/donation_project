from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    CollectViewSet,
    PaymentViewSet,
    PaymentCommentViewSet,
    PaymentLikeViewSet,
    RegisterView, redirect_short_link
)

v1_router = DefaultRouter()

# Основной ресурс
v1_router.register(r'collects', CollectViewSet)

# Вложенные ресурсы: payments, comments, likes
payment_prefix = r'collects/(?P<collect_id>\d+)/payments'
v1_router.register(payment_prefix, PaymentViewSet, basename='collect-payments')
v1_router.register(rf'{payment_prefix}/(?P<payment_id>\d+)/comments', PaymentCommentViewSet, basename='payment-comments')
v1_router.register(rf'{payment_prefix}/(?P<payment_id>\d+)/likes', PaymentLikeViewSet, basename='payment-likes')

urlpatterns = [
    path('', include(v1_router.urls)),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
]
