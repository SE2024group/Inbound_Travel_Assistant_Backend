# api/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import EchoSerializer, LoginSerializer, LoginResponseSerializer, UserInfoSerializer, OCRSerializer
from django.conf import settings
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.authentication import TokenAuthentication, SessionAuthentication
from django.contrib.auth import get_user_model
from PIL import Image
import uuid
import base64
import requests
import io
import os
import random

User = get_user_model()


class EchoView(APIView):
    def post(self, request):
        serializer = EchoSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            return Response({'username': username}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
# web/api/views.py

from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token  # 使用 Token 认证
from .serializers import (
    RegisterSerializer, LoginSerializer, UserSerializer,
    BrowsingHistorySerializer, LikeHistorySerializer,
    FavoriteHistorySerializer, CommentHistorySerializer
)
from .models import BrowsingHistory, LikeHistory, FavoriteHistory, CommentHistory

User = get_user_model()

# 注册视图
class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # 创建 Token
        token, created = Token.objects.get_or_create(user=user)
        return Response({
            "user": UserSerializer(user, context=self.get_serializer_context()).data,
            "token": token.key
        }, status=status.HTTP_201_CREATED)

from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import authenticate

# 登录视图
class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        username = serializer.validated_data['username']
        password = serializer.validated_data['password']

        # 使用 django.contrib.auth.authenticate 对用户名和密码进行数据库验证
        user = authenticate(username=username, password=password)
        if not user:
            return Response({"error": "Invalid username or password."}, status=status.HTTP_400_BAD_REQUEST)

        # 登录成功，获取或创建Token
        token, created = Token.objects.get_or_create(user=user)
        user_data = UserSerializer(user).data
        return Response({
            "user": user_data,
            "token": token.key
        }, status=status.HTTP_200_OK)

# 登出视图
class LogoutView(APIView):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            # 删除用户的所有 Token
            request.user.auth_token.delete()
        except:
            return Response({'error': 'Token not found.'}, status=status.HTTP_400_BAD_REQUEST)

        return Response({"message": "Logged out successfully."}, status=status.HTTP_200_OK)

# 用户详细信息视图
class UserDetailView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

# 浏览历史视图
class BrowsingHistoryListView(generics.ListAPIView):
    serializer_class = BrowsingHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return BrowsingHistory.objects.filter(user=self.request.user)

# 点赞历史视图
class LikeHistoryListView(generics.ListAPIView):
    serializer_class = LikeHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return LikeHistory.objects.filter(user=self.request.user)

# 收藏历史视图
class FavoriteHistoryListView(generics.ListAPIView):
    serializer_class = FavoriteHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return FavoriteHistory.objects.filter(user=self.request.user)

# 评论历史视图
class CommentHistoryListView(generics.ListAPIView):
    serializer_class = CommentHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return CommentHistory.objects.filter(user=self.request.user)

class OCRView(APIView):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = OCRSerializer(data=request.data)
        if serializer.is_valid():
            image = serializer.validated_data['image']

            image_content = image.read()
            base64_image = base64.b64encode(image_content).decode('utf-8')

            content_type = image.content_type
            print(content_type)

            # 调用 OCR API
            ocr_api_url = 'https://api.ocr.space/parse/image'
            api_key = settings.OCR_API_KEY

            payload = {
                'language': 'chs',
                'isOverlayRequired': 'true',
                'base64Image': f'data:{content_type};base64,{base64_image}',
            }
            headers = {
                'apikey': api_key,
            }

            try:
                response = requests.post(ocr_api_url, data=payload, headers=headers, timeout=30)
                response.raise_for_status()
                ocr_result = response.json()
                print(ocr_result)
            except requests.RequestException as e:
                return Response({'error': 'OCR API request failed'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

            # 检查 OCR API 是否成功
            if ocr_result.get('OCRExitCode') != 1:
                return Response({
                    'error': 'OCR processing failed',
                    'details': ocr_result.get('ErrorMessage') or ocr_result.get('ErrorDetails')
                }, status=status.HTTP_400_BAD_REQUEST)

            result_data = []
            parsed_results = ocr_result.get('ParsedResults', [])

            for result in parsed_results:
                text_overlay = result.get('TextOverlay', {})
                lines = text_overlay.get('Lines', [])

                for line in lines:
                    line_text = line.get('LineText', '')
                    words = line.get('Words', [])
                    # 如果行长度小于2，跳过
                    if len(line_text) < 2:
                        continue

                    # 定义一个函数检查字符是否为中文
                    def is_chinese_char(c):
                        return '\u4e00' <= c <= '\u9fff'

                    i = 0
                    while i < len(line_text):
                        char = line_text[i]
                        # 如果当前字符不是中文，则跳过这个字符
                        if not is_chinese_char(char):
                            i += 1
                            continue

                        # 当前字符是中文，尝试匹配长度在2到6之间的子串
                        matched = False
                        for sub_len in range(6, 1, -1):  # 优先尝试较长的子串
                            if i + sub_len <= len(line_text):
                                sub_str = line_text[i:i+sub_len]

                                # 检查子串中是否有非中文字符
                                if any(not is_chinese_char(c) for c in sub_str):
                                    # 遇到非中文字符，从下一个字符继续
                                    i += 1
                                    matched = True
                                    break

                                # 在数据库中查找该子串对应的菜品
                                dish = Dish.objects.filter(name=sub_str).first()
                                if dish:
                                    # 找到匹配词条
                                    # 计算子串的 bounding box
                                    # 假设 words 的长度与 line_text 相同，且一一对应
                                    # 子串对应的words切片为 words[i:i+sub_len]
                                    substring_words = words[i:i+sub_len]
                                    min_left = min(w['Left'] for w in substring_words)
                                    min_top = min(w['Top'] for w in substring_words)
                                    max_right = max(w['Left'] + w['Width'] for w in substring_words)
                                    max_bottom = max(w['Top'] + w['Height'] for w in substring_words)

                                    bounding_box = {
                                        'top_left': {'x': min_left, 'y': min_top},
                                        'bottom_right': {'x': max_right, 'y': max_bottom}
                                    }

                                    # 获取菜品图片
                                    image_url = ''
                                    if dish.images.exists():
                                        image_url = dish.images.first().image_url

                                    result_data.append({
                                        'linetext_substring': sub_str,
                                        'ID': dish.id,
                                        'en_name': dish.name_en,
                                        'image': image_url,
                                        'bounding_box': bounding_box
                                    })

                                    # 如果用户已认证，记录浏览历史
                                    if request.user.is_authenticated:
                                        BrowsingHistory.objects.create(user=request.user, dish=dish)

                                    # 匹配成功后，从下一个子串结束的位置继续
                                    i += sub_len
                                    matched = True
                                    break
                        if not matched:
                            # 没有匹配成功，也没有遇到非中文字符的打断，则 i += 1
                            i += 1

            print(result_data)
            return Response({'results': result_data}, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

from .models import Dish
from .serializers import DishDetailSerializer

class DishDetailView(APIView):
    authentication_classes = [TokenAuthentication, SessionAuthentication]
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, pk):
        try:
            dish = Dish.objects.get(pk=pk)
        except Dish.DoesNotExist:
            return Response({'error': 'Dish not found.'}, status=status.HTTP_404_NOT_FOUND)

        serializer = DishDetailSerializer(dish)

        # 如果用户已认证，记录浏览历史
        if request.user.is_authenticated:
            BrowsingHistory.objects.create(user=request.user, dish=dish)

        return Response(serializer.data, status=status.HTTP_200_OK)


from .serializers import VoiceTranslationSerializer

class VoiceTranslationView(APIView):
    """
    语音翻译公开 API 端点。
    接受语音文件和 isChineseMode 参数，返回固定的文字结果。
    """
    # 允许所有用户访问，包括匿名用户
    permission_classes = []  # 或者使用 [AllowAny]

    def post(self, request, format=None):
        serializer = VoiceTranslationSerializer(data=request.data)
        if serializer.is_valid():
            voice_file = serializer.validated_data['voice_file']
            is_chinese_mode = serializer.validated_data['isChineseMode']
            
            # 这里暂时不实现实际的语音识别逻辑，直接返回固定的文字
            response_data = {
                "code": 200,
                "message": "上传成功",
                "data": {
                    "text": "这是服务器返回的文本内容",
                    "isChineseMode": is_chinese_mode
                }
            }
            return Response(response_data, status=status.HTTP_200_OK)
        else:
            # 返回序列化器的错误信息
            return Response({
                "code": 400,
                "message": "上传失败",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)