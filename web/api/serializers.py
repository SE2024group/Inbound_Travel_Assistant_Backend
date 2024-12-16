# web/api/serializers.py

from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import (
    Dish, Image, Tag, BrowsingHistory, LikeHistory, 
    FavoriteHistory, CommentHistory, DietaryPreference
)

User = get_user_model()

class EchoSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)

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

class LoginResponseSerializer(serializers.Serializer):
    token = serializers.CharField()

class UserInfoSerializer(serializers.Serializer):
    avatar = serializers.URLField()
    nickname = serializers.CharField()

class ErrorResponseSerializer(serializers.Serializer):
    error = serializers.CharField()

class OCRSerializer(serializers.Serializer):
    image = serializers.ImageField(required=True)

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

class DishSearchSerializer(serializers.Serializer):
    tags = serializers.ListField(
        child=serializers.CharField(max_length=50),
        required=True,
        help_text="需要检索的标签列表，如 ['辣', '川菜']"
    )

class DietaryPreferenceSerializer(serializers.ModelSerializer):
    tag = serializers.SlugRelatedField(
        slug_field='name_en',
        queryset=Tag.objects.all(),
        help_text="标签名称，例如 'Vegetarian', 'Halal'"
    )
    preference = serializers.ChoiceField(
        choices=DietaryPreference.PREFERENCE_CHOICES,
        help_text="偏好状态，取值为 'LIKE', 'DISLIKE', 'OTHER'"
    )

    class Meta:
        model = DietaryPreference
        fields = ['tag', 'preference']

class UserSerializer(serializers.ModelSerializer):
    dietary_preferences = DietaryPreferenceSerializer(
        many=True,
        required=False,
    )

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'nickname',
            'avatar', 'personality_description',
            'signup_date', 'religious_belief',
            'dietary_preferences'
        ]
        read_only_fields = ['id', 'signup_date']

    def update(self, instance, validated_data):
        # 处理 dietary_preferences
        dietary_preferences_data = validated_data.pop('dietary_preferences', None)
        if dietary_preferences_data is not None:
            # 清除现有的偏好
            DietaryPreference.objects.filter(user=instance).delete()

            # 创建新的偏好
            for pref in dietary_preferences_data:
                tag = pref.get('tag')
                preference = pref.get('preference')
                DietaryPreference.objects.create(user=instance, tag=tag, preference=preference)

        # 更新其他字段
        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        instance.save()
        return instance

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
        max_size = 20 * 1024 * 1024  # 20MB
        min_size = 1024  # 1KB
        if value.size > max_size:
            raise serializers.ValidationError("文件大小超过限制（20MB）。")
        if value.size < min_size:
            raise serializers.ValidationError("文件大小不足（1KB）。")
        return value

class TextTranslationSerializer(serializers.Serializer):
    text = serializers.CharField(required=True, help_text="需要翻译的文本")
    isChineseMode = serializers.BooleanField(required=True, help_text="是否为中文模式，True表示原文为中文")

class AdvancedSearchSerializer(serializers.Serializer):
    text = serializers.CharField(required=True, help_text="搜索文本，可以是中英文菜名、描述或标签名称。")
    filter = DietaryPreferenceSerializer(many=True, required=False, help_text="可选的过滤器列表，包含标签和偏好。")