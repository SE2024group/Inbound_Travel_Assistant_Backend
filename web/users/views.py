# web/users/views.py

from rest_framework import generics, status
from rest_framework.permissions import IsAuthenticated
from rest_framework.views import APIView
from rest_framework.response import Response
from .serializers import UserAvatarSerializer
from .models import CustomUser
from django.shortcuts import get_object_or_404
from rest_framework.parsers import MultiPartParser, FormParser
from qcloud_cos import CosConfig, CosS3Client
from qcloud_cos.cos_exception import CosServiceError
import uuid
import os
import logging

# 初始化COS客户端
def get_cos_client():
    config = CosConfig(
        Region=settings.COS_REGION,
        SecretId=settings.COS_SECRET_ID,
        SecretKey=settings.COS_SECRET_KEY,
        Token=None,  # 使用长期密钥
        Scheme='https'
    )
    return CosS3Client(config)

class UserAvatarUploadView(APIView):
    """
    API视图，允许用户上传和更新自己的头像。
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def put(self, request, format=None):
        user = request.user
        serializer = UserAvatarSerializer(
            user,
            data=request.data,
            partial=True,
            context={
                'cos_client': get_cos_client(),
                'cos_bucket': settings.COS_BUCKET,
                'cos_region': settings.COS_REGION,
                'cos_base_url': settings.COS_BASE_URL
            }
        )
        if serializer.is_valid():
            serializer.save()
            return Response({
                "code": 200,
                "message": "头像上传成功",
                "data": {
                    "avatar": user.avatar
                }
            }, status=status.HTTP_200_OK)
        return Response({
            "code": 400,
            "message": "请求无效",
            "errors": serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)
