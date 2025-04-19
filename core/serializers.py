from datetime import timezone, datetime

from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Collect, Payment, PaymentLike, PaymentComment


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name']


class PaymentLikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentLike
        fields = ['id', 'created_at']
        read_only_fields = ['user', 'created_at']

    def validate(self, attrs):
        user = self.context['request'].user
        payment = self.context['view'].get_payment()

        if PaymentLike.objects.filter(user=user, payment=payment).exists():
            raise serializers.ValidationError("Вы уже ставили лайк на этот платёж.")
        return attrs


class PaymentCommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentComment
        fields = ['id', 'user', 'text', 'created_at']
        read_only_fields = ['user']

    def validate(self, attrs):
        user = self.context['request'].user
        payment = self.context['view'].get_payment()

        if PaymentComment.objects.filter(user=user, payment=payment).exists():
            raise serializers.ValidationError("Вы уже оставили комментарий к этому платежу.")
        return attrs


class PaymentSerializer(serializers.ModelSerializer):
    donor = UserSerializer(read_only=True)
    # collect = serializers.PrimaryKeyRelatedField(queryset=Collect.objects.all())
    likes_count = serializers.SerializerMethodField()
    comments = PaymentCommentSerializer(many=True, read_only=True)

    class Meta:
        model = Payment
        fields = ['id', 'amount', 'created_at', 'donor', 'likes_count', 'comments']

    def get_likes_count(self, obj):
        return obj.likes.count()


class CollectSerializer(serializers.ModelSerializer):
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
        # Общая проверка чисел
        for field in ['goal_amount', 'collected_amount']:
            value = data.get(field)
            if value is not None and value < 0:
                raise serializers.ValidationError({field: f"Значение '{field}' должно быть больше нуля."})

        # Проверка даты
        end_datetime = data.get('end_datetime')
        if end_datetime and end_datetime < datetime.now(timezone.utc):
            raise serializers.ValidationError({
                'end_datetime': "Нельзя ставить дату завершения в прошлом."
            })

        return data


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    password2 = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ['username', 'password', 'password2', 'first_name', 'last_name', 'email']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Пароли не совпадают."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user
