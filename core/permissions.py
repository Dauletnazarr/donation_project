from rest_framework.permissions import SAFE_METHODS, BasePermission


class OwnerOrReadOnly(BasePermission):
    """
    Базовое разрешение: только владелец объекта может изменять.
    Остальным доступен только просмотр.
    """
    owner_field = None  # <- конкретное имя поля задаётся в наследнике

    def has_object_permission(self, request, view, obj):
        if request.method in SAFE_METHODS:
            return True

        owner = getattr(obj, self.owner_field, None)
        return owner == request.user


class AuthorOrReadOnly(OwnerOrReadOnly):
    owner_field = 'author'


class DonorOrReadOnly(OwnerOrReadOnly):
    owner_field = 'donor'


class IsDonatorOfCollect(BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        if not user.is_authenticated:
            return False

        # Получаем сбор, связанный с этим платежом
        collect = obj.payment.collect
        return collect.payments.filter(donor=user).exists()
