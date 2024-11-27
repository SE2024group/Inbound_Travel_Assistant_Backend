# api/serializers.py

from rest_framework import serializers
import uuid

class EchoSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)

class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)

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
        fields = ['id', 'name']

class ImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = Image
        fields = ['image_url']

class DishDetailSerializer(serializers.ModelSerializer):
    images = ImageSerializer(many=True, read_only=True)
    tags = TagSerializer(many=True, read_only=True)

    class Meta:
        model = Dish
        fields = ['id', 'name', 'description', 'images', 'tags']
