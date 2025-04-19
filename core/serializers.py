from datetime import timezone, datetime

from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Collect, Payment, PaymentLike, PaymentComment


class UserSerializer(serializers.ModelSerializer):
    """
    Сериализатор для представления данных пользователя.

    Используется для отображения ограниченной информации о пользователе.
    """
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']


class PaymentLikeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания и отображения лайков к платежам.

    Валидация не позволяет одному пользователю лайкать один платёж более одного раза.
    """
    class Meta:
        model = PaymentLike
        fields = ['id', 'created_at']
        read_only_fields = ['user', 'created_at']

    def validate(self, attrs):
        """
        Проверяет, поставил ли пользователь уже лайк на данный платёж.
        """
        user = self.context['request'].user
        payment = self.context['view'].get_payment()

        if PaymentLike.objects.filter(user=user, payment=payment).exists():
            raise serializers.ValidationError("Вы уже ставили лайк на этот платёж.")
        return attrs


class PaymentCommentSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания и отображения комментариев к платежам.

    Валидация запрещает оставлять более одного комментария на один платёж от одного пользователя.
    """
    class Meta:
        model = PaymentComment
        fields = ['id', 'user', 'text', 'created_at']
        read_only_fields = ['user']

    def validate(self, attrs):
        """
        Проверяет, оставил ли пользователь уже комментарий на данный платёж.
        """
        user = self.context['request'].user
        payment = self.context['view'].get_payment()

        if PaymentComment.objects.filter(user=user, payment=payment).exists():
            raise serializers.ValidationError("Вы уже оставили комментарий к этому платежу.")
        return attrs


class PaymentSerializer(serializers.ModelSerializer):
    """
    Сериализатор для отображения информации о платеже.

    Включает количество лайков и список комментариев.
    """
    donor = UserSerializer(read_only=True)
    likes_count = serializers.SerializerMethodField()
    comments = PaymentCommentSerializer(many=True, read_only=True)

    class Meta:
        model = Payment
        fields = ['id', 'amount', 'created_at', 'donor', 'likes_count', 'comments']

    def get_likes_count(self, obj):
        """
        Возвращает количество лайков для данного платежа.
        """
        return obj.likes.count()


class CollectSerializer(serializers.ModelSerializer):
    """
    Сериализатор для создания и отображения сборов.

    Проверяет положительность сумм и то, что дата окончания не в прошлом.
    """
    author = UserSerializer(read_only=True)
    payments = PaymentSerializer(many=True, read_only=True)

    class Meta:
        model = Collect
        fields = [
            'id', 'author', 'title', 'occasion', 'description',
            'goal_amount', 'collected_amount', 'donors_count',
            'cover_image', 'end_datetime', 'created_at', 'payments'
        ]

    def validate(self, data):
        """
        Выполняет валидацию:
        - goal_amount и collected_amount должны быть неотрицательными
        - end_datetime не должен быть в прошлом
        """
        for field in ['goal_amount', 'collected_amount']:
            value = data.get(field)
            if value is not None and value < 0:
                raise serializers.ValidationError({field: f"Значение '{field}' должно быть больше нуля."})

        end_datetime = data.get('end_datetime')
        if end_datetime and end_datetime < datetime.now(timezone.utc):
            raise serializers.ValidationError({
                'end_datetime': "Нельзя ставить дату завершения в прошлом."
            })

        return data


class RegisterSerializer(serializers.ModelSerializer):
    """
    Сериализатор для регистрации нового пользователя.

    Проверяет совпадение паролей, обязательность и уникальность email.
    """
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['username', 'password', 'password2', 'first_name', 'last_name', 'email']

    def validate(self, attrs):
        """
        Валидация паролей и email:
        - пароли должны совпадать
        - email обязателен и должен быть уникальным
        """
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Пароли не совпадают."})

        if not attrs.get('email'):
            raise serializers.ValidationError({"email": "Это поле обязательно."})

        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"email": "Этот email уже зарегистрирован."})

        return attrs

    def create(self, validated_data):
        """
        Создаёт нового пользователя, удаляя поле подтверждения пароля.
        """
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user
