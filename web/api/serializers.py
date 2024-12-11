# api/serializers.py

from rest_framework import serializers
import uuid

from django.contrib.auth import get_user_model
from .models import Dish, Image, Tag, BrowsingHistory, LikeHistory, FavoriteHistory, CommentHistory


User = get_user_model()


class EchoSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

class LoginResponseSerializer(serializers.Serializer):
    token = serializers.CharField()

class UserInfoSerializer(serializers.Serializer):
    avatar = serializers.URLField()
    nickname = serializers.CharField()

class ErrorResponseSerializer(serializers.Serializer):
    error = serializers.CharField()

class OCRSerializer(serializers.Serializer):
    image = serializers.ImageField(required=True)

from .models import Dish, Image, Tag

class TagSerializer(serializers.ModelSerializer):
    class Meta:
        model = Tag
        fields = ['id', 'name', 'name_en']

class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ['image_url']

class DishDetailSerializer(serializers.ModelSerializer):
    images = ImageSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Dish
        fields = [
            'id', 
            'name', 
            'name_en', 
            'description', 
            'description_en', 
            'images', 
            'tags'
        ]

class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'nickname', 'avatar', 'personality_description']
        read_only_fields = ['id']

class BrowsingHistorySerializer(serializers.ModelSerializer):
    dish = serializers.StringRelatedField()

    class Meta:
        model = BrowsingHistory
        fields = ['id', 'dish', 'timestamp']
        read_only_fields = ['id', 'timestamp']

class LikeHistorySerializer(serializers.ModelSerializer):
    dish = serializers.StringRelatedField()

    class Meta:
        model = LikeHistory
        fields = ['id', 'dish', 'timestamp']
        read_only_fields = ['id', 'timestamp']

class FavoriteHistorySerializer(serializers.ModelSerializer):
    dish = serializers.StringRelatedField()

    class Meta:
        model = FavoriteHistory
        fields = ['id', 'dish', 'timestamp']
        read_only_fields = ['id', 'timestamp']

class CommentHistorySerializer(serializers.ModelSerializer):
    dish = serializers.StringRelatedField()

    class Meta:
        model = CommentHistory
        fields = ['id', 'dish', 'comment', 'timestamp']
        read_only_fields = ['id', 'timestamp']

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ['username', 'password', 'password2', 'nickname', 'avatar', 'personality_description']

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(write_only=True, required=True, style={'input_type': 'password'})

    def validate(self, attrs):
        from django.contrib.auth import authenticate
        user = authenticate(username=attrs['username'], password=attrs['password'])
        if not user:
            raise serializers.ValidationError("Invalid username or password.")
        attrs['user'] = user
        return attrs


from django.core.validators import FileExtensionValidator

class VoiceTranslationSerializer(serializers.Serializer):
    voice_file = serializers.FileField(
        required=True,
        allow_empty_file=False,
        help_text="上传语音文件",
        validators=[
            FileExtensionValidator(allowed_extensions=['wav', 'mp3', 'm4a']),
        ]
    )
    isChineseMode = serializers.BooleanField(
        required=True,
        help_text="是否为中文模式"
    )

    def validate_voice_file(self, value):
        max_size = 20 * 1024 * 1024  # 10MB
        min_size = 1024
        if value.size > max_size:
            raise serializers.ValidationError("文件大小超过限制（10MB）。")
        if value.size < min_size:
            raise serializers.ValidationError("文件大小不足（1KB）。")
        return value

