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
