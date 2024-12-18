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

from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token  # 使用 Token 认证
from .serializers import (
    RegisterSerializer, LoginSerializer, UserSerializer,
    BrowsingHistorySerializer, LikeHistorySerializer,
    FavoriteHistorySerializer, CommentHistorySerializer
)
from .models import BrowsingHistory, LikeHistory, FavoriteHistory, CommentHistory
from datetime import date


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
        # 设置用户的注册日期
        user.signup_date = date.today()
        user.save()

        token, created = Token.objects.get_or_create(user=user)
        return Response({
            "user": UserSerializer(user, context=self.get_serializer_context()).data,
            "token": token.key
        }, status=status.HTTP_201_CREATED)

from rest_framework.permissions import IsAuthenticated
from django.contrib.auth import authenticate

# web/api/views.py 中 LoginView

class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        username = serializer.validated_data['username']
        password = serializer.validated_data['password']

        from django.contrib.auth import authenticate
        user = authenticate(username=username, password=password)
        if not user:
            return Response({"error": "Invalid username or password."}, status=status.HTTP_401_UNAUTHORIZED)

        # 登录成功，获取或创建Token
        from rest_framework.authtoken.models import Token
        token, created = Token.objects.get_or_create(user=user)
        user_data = UserSerializer(user).data
        return Response({
            "token": token.key,
            "user": user_data
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


from rest_framework.permissions import IsAuthenticated
from rest_framework import generics


class UpdateUserPreferencesView(APIView):
    """
    允许已认证的用户更新其宗教信仰和饮食偏好。
    """
    permission_classes = [IsAuthenticated]

    def patch(self, request, format=None):
        user = request.user
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                "message": "Preferences updated successfully.",
                "user": serializer.data
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "code": 400,
                "message": "上传失败",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)


# 用户详细信息视图
class UserDetailView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user
        
    def update(self, request, *args, **kwargs):
        print("Update user info")
        partial = kwargs.pop('partial', True)  # 允许部分更新
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # 日志记录
        if 'avatar' in request.FILES:
            print(f"User {instance.username} uploaded avatar: {instance.avatar.url}")
            logger.info(f"User {instance.username} uploaded avatar: {instance.avatar.url}")

        return Response(serializer.data)

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
            # 获取菜品
            dish = Dish.objects.get(pk=pk)
        except Dish.DoesNotExist:
            return Response({'error': 'Dish not found.'}, status=status.HTTP_404_NOT_FOUND)

        # 创建标签序列化器，并传递当前用户信息
        serializer = DishDetailSerializer(dish, context={'user': request.user})

        # 如果用户已认证，记录浏览历史
        if request.user.is_authenticated:
            # 记录用户浏览的菜品
            BrowsingHistory.objects.create(user=request.user, dish=dish)

        return Response(serializer.data, status=status.HTTP_200_OK)

from .serializers import DishSearchSerializer
from .models import Dish, Tag

class DishSearchView(APIView):
    """
    接受标签列表，检索包含所有这些标签的菜品，返回菜品ID列表。
    """
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        serializer = DishSearchSerializer(data=request.data)
        if serializer.is_valid():
            tags = serializer.validated_data['tags']

            # 从数据库检索这些标签对象，如果有一个标签不存在，则结果可能为空
            # 首先检测标签是否存在
            existing_tags = Tag.objects.filter(name__in=tags)
            if existing_tags.count() != len(tags):
                # 有些标签在数据库中不存在，则无匹配菜品
                return Response({
                    "code": 200,
                    "message": "搜索完成",
                    "data": {
                        "results": []
                    }
                }, status=status.HTTP_200_OK)

            # 进行AND查询：逐步过滤菜品
            dish_qs = Dish.objects.all()
            for tag_name in tags:
                dish_qs = dish_qs.filter(tags__name=tag_name)
            
            # 获取匹配菜品的ID列表
            dish_ids = list(dish_qs.values_list('id', flat=True))

            return Response({
                "code": 200,
                "message": "搜索完成",
                "data": {
                    "results": dish_ids
                }
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                "code": 400,
                "message": "请求无效",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

from .serializers import TagSerializer

class TagListView(generics.ListAPIView):
    """
    API 视图，返回所有标签的列表。
    """
    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]  # 任何人都可以访问此 API

import tempfile
import whisper
from opencc import OpenCC
from .serializers import VoiceTranslationSerializer
import logging
from .utils import translate_text  # 导入翻译函数

# 初始化转换器，从繁体中文转换到简体中文
converter = OpenCC('t2s')

# 加载 Whisper 模型（CPU 版本）
model = None # whisper.load_model("base")  # "base" 模型适用于 CPU，较小且速度较快
logger = logging.getLogger(__name__)

class VoiceTranslationView(APIView):
    """
    语音翻译公开 API 端点。
    接受语音文件和 isChineseMode 参数，返回中英文文字结果。
    """
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        serializer = VoiceTranslationSerializer(data=request.data)
        if serializer.is_valid():
            voice_file = serializer.validated_data['voice_file']
            is_chinese_mode = serializer.validated_data['isChineseMode']

            print("is_chinese_mode:", is_chinese_mode)
            
            # 使用临时文件保存上传的语音文件
            with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(voice_file.name)[1]) as temp_file:
                for chunk in voice_file.chunks():
                    temp_file.write(chunk)
                temp_file_path = temp_file.name
            
            try:
                # 选择语言
                language = "zh" if is_chinese_mode else "en"
                
                # 使用 Whisper 模型进行转录
                # result = model.transcribe(temp_file_path, language=language)
                transcribed_text = '使用 Whisper Model 进行 Transform' # result['text'].strip()
                
                # 如果是中文模式，进行简繁体转换
                if is_chinese_mode:
                    transcribed_text = converter.convert(transcribed_text)
                
                print(f"Transcribed text: {transcribed_text}")

                logger.info(f"Transcribed text: {transcribed_text}")
                
                # 调用翻译 API 将文本翻译成目标语言
                # 如果 isChineseMode 是 True，翻译到英文；否则翻译到中文
                if is_chinese_mode:
                    translated_text = translate_text(transcribed_text, from_lang="ZH", to_lang="EN")
                else:
                    translated_text = translate_text(transcribed_text, from_lang="EN", to_lang="ZH")
                
                print(f"Translated text: {translated_text}")
                
                response_data = {
                    "code": 200,
                    "message": "上传成功",
                    "data": {
                        "cn_text": transcribed_text if is_chinese_mode else translated_text,
                        "en_text": transcribed_text if not is_chinese_mode else translated_text,
                        "isChineseMode": is_chinese_mode
                    }
                }
                                
                return Response(response_data, status=status.HTTP_200_OK)
            
            except Exception as e:
                logger.error(f"Error during voice transcription or translation: {str(e)}")
                return Response({
                    "code": 500,
                    "message": "服务器内部错误",
                    "errors": str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            finally:
                # 删除临时文件
                os.remove(temp_file_path)
        else:
            logger.warning(f"Voice translation upload failed: {serializer.errors}")
            return Response({
                "code": 400,
                "message": "上传失败",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

from .serializers import TextTranslationSerializer

class TextTranslationView(APIView):
    """
    文本翻译公开 API 端点。
    接受文本和 isChineseMode 参数，返回中英文文字结果。
    """
    permission_classes = [AllowAny]

    def post(self, request, format=None):
        serializer = TextTranslationSerializer(data=request.data)
        if serializer.is_valid():
            text = serializer.validated_data['text']
            is_chinese_mode = serializer.validated_data['isChineseMode']

            logger.info(f"Received text translation request. isChineseMode: {is_chinese_mode}")

            try:

                # 如果是中文模式: 原文中文 -> 译文英文
                # 如果是英文模式: 原文英文 -> 译文中文
                if is_chinese_mode:
                    # 中文 -> 英文
                    translated_text = translate_text(text, from_lang="ZH", to_lang="EN")
                    cn_text = text
                    en_text = translated_text
                else:
                    # 英文 -> 中文
                    translated_text = translate_text(text, from_lang="EN", to_lang="ZH")
                    cn_text = translated_text
                    en_text = text

                logger.info(f"Original text: {text}")
                logger.info(f"Translated text: {translated_text}")

                response_data = {
                    "code": 200,
                    "message": "上传成功",
                    "data": {
                        "cn_text": cn_text,
                        "en_text": en_text,
                        "isChineseMode": is_chinese_mode
                    }
                }

                return Response(response_data, status=status.HTTP_200_OK)

            except Exception as e:
                logger.error(f"Error during text translation: {str(e)}")
                return Response({
                    "code": 500,
                    "message": "服务器内部错误",
                    "errors": str(e)
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        else:
            logger.warning(f"Text translation request failed: {serializer.errors}")
            return Response({
                "code": 400,
                "message": "上传失败",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

from .serializers import AdvancedSearchSerializer
from django.db.models import Q, Count
# 进阶搜索视图
class AdvancedSearchView(APIView):
    """
    进阶搜索API：
    - 接收一段文本，可能是中英文菜名、描述或标签名。
    - 可选的filter字段，用于进一步过滤结果。
    - 返回匹配的菜品ID列表，按照偏好排序。
    """
    permission_classes = [AllowAny]
    
    def post(self, request, format=None):
        serializer = AdvancedSearchSerializer(data=request.data)
        if serializer.is_valid():
            text = serializer.validated_data['text']
            filter_data = serializer.validated_data.get('filter', [])
            
            # 初步搜索：根据文本匹配菜名、描述或标签名称
            dishes = Dish.objects.filter(
                Q(name__icontains=text) |
                Q(name_en__icontains=text) |
                Q(description__icontains=text) |
                Q(description_en__icontains=text) |
                Q(tags__name__icontains=text) |
                Q(tags__name_en__icontains=text)
            ).distinct()
            
            logger.debug(f"初步搜索结果数量：{dishes.count()}")
            
            if filter_data:
                # 处理过滤器
                dislike_tags = []
                like_tags = []
                for pref in filter_data:
                    tag = pref.get('tag')
                    preference = pref.get('preference')
                    if preference == 'DISLIKE':
                        dislike_tags.append(tag)
                    elif preference == 'LIKE':
                        like_tags.append(tag)
                    # 'OTHER' 偏好不做处理
                
                logger.debug(f"过滤器 - 喜爱标签: {like_tags}, 不喜爱标签: {dislike_tags}")
                
                if dislike_tags:
                    # 排除包含任何不喜爱标签的菜品
                    dishes = dishes.exclude(tags__in=dislike_tags)
                    logger.debug(f"应用DISLIKE过滤后结果数量：{dishes.count()}")
                
                if like_tags:
                    # 注释每个菜品包含喜爱标签的数量
                    dishes = dishes.annotate(
                        like_count=Count('tags', filter=Q(tags__in=like_tags))
                    ).order_by('-like_count')
                    logger.debug(f"应用LIKE过滤后结果数量：{dishes.count()}")
                else:
                    # 如果没有LIKE标签，则不需要排序
                    pass
            
            # 获取菜品ID列表
            dish_ids = list(dishes.values_list('id', flat=True))
            
            logger.debug(f"最终返回的菜品ID列表：{dish_ids}")
            
            return Response({
                "code": 200,
                "message": "搜索完成",
                "data": {
                    "results": dish_ids
                }
            }, status=status.HTTP_200_OK)
        else:
            logger.error(f"进阶搜索请求无效：{serializer.errors}")
            return Response({
                "code": 400,
                "message": "请求无效",
                "errors": serializer.errors
            }, status=status.HTTP_400_BAD_REQUEST)

from .serializers import FavoriteSerializer
from .models import Dish, FavoriteHistory
from django.shortcuts import get_object_or_404

class FavoriteToggleView(APIView):
    """
    API 视图，处理用户收藏与取消收藏某道菜的操作。
    POST 请求用于收藏，DELETE 请求用于取消收藏。
    """
    permission_classes = [IsAuthenticated]

    def post(self, request, dish_id):
        """
        收藏指定ID的菜品。
        """
        serializer = FavoriteSerializer(data={'dish_id': dish_id})
        serializer.is_valid(raise_exception=True)
        dish_id = serializer.validated_data['dish_id']
        dish = get_object_or_404(Dish, pk=dish_id)
        user = request.user

        # 检查是否已经收藏
        if FavoriteHistory.objects.filter(user=user, dish=dish).exists():
            return Response({'detail': '该菜品已在收藏列表中。'}, status=status.HTTP_400_BAD_REQUEST)

        # 添加到收藏列表
        FavoriteHistory.objects.create(user=user, dish=dish)
        return Response({'detail': '菜品已成功添加到收藏列表。'}, status=status.HTTP_201_CREATED)

    def delete(self, request, dish_id):
        """
        取消收藏指定ID的菜品。
        """
        dish = get_object_or_404(Dish, pk=dish_id)
        user = request.user

        try:
            favorite = FavoriteHistory.objects.get(user=user, dish=dish)
            favorite.delete()
            return Response({'detail': '菜品已成功从收藏列表中移除。'}, status=status.HTTP_200_OK)
        except FavoriteHistory.DoesNotExist:
            return Response({'detail': '该菜品不在您的收藏列表中。'}, status=status.HTTP_400_BAD_REQUEST)

from .serializers import FavoriteDishSerializer
from .models import FavoriteHistory

class FavoriteListView(generics.ListAPIView):
    """
    API 视图，获取当前用户的收藏列表。
    返回收藏的菜品的图片、英文名称、中文名称和ID。
    """
    serializer_class = FavoriteDishSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Dish.objects.filter(favorite_histories__user=user).distinct()


from .serializers import (
    CommentUploadSerializer,
    CommentSerializer,
)
from .models import CommentHistory, CommentImage
from rest_framework.parsers import MultiPartParser, FormParser

class CommentUploadView(APIView):
    """
    API 视图，允许用户上传评论，包括评论内容、评分分数和最多9张图片。
    """
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request, format=None):
        serializer = CommentUploadSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            comment = serializer.save()
            read_serializer = CommentSerializer(comment)
            return Response(read_serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class DishCommentsView(generics.ListAPIView):
    """
    API 视图，获取指定菜品的所有评论。
    """
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        dish_id = self.kwargs.get('dish_id')
        return CommentHistory.objects.filter(dish_id=dish_id).order_by('-timestamp')

from .serializers import UserCommentHistorySerializer, CommentSerializer
class UserCommentHistoryView(generics.ListAPIView):
    """
    API 视图，获取当前用户的评论历史。
    返回每条评论所属的菜品的ID、中英文名称及图片。
    """
    serializer_class = UserCommentHistorySerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return CommentHistory.objects.filter(user=user).order_by('-timestamp')


from .permissions import IsOwnerOrAdmin

class CommentDeleteView(generics.DestroyAPIView):
    """
    API 视图，允许用户删除自己的评论，管理员可以删除任何评论。
    """
    queryset = CommentHistory.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated, IsOwnerOrAdmin]

    def get_object(self):
        comment_id = self.kwargs.get('comment_id')
        comment = get_object_or_404(CommentHistory, pk=comment_id)
        self.check_object_permissions(self.request, comment)
        return comment

    def delete(self, request, *args, **kwargs):
        """
        重写destroy方法，以返回自定义的删除成功消息。
        """
        instance = self.get_object()
        self.perform_destroy(instance)
        return Response({'detail': '评论已成功删除。'}, status=status.HTTP_200_OK)




class DishDetailView(APIView):
    """
    API 视图，获取指定ID的菜品详情。
    返回菜品的详细信息，包括标签的喜爱状态。
    """
    permission_classes = [IsAuthenticatedOrReadOnly]

    def get(self, request, pk):
        dish = get_object_or_404(Dish, pk=pk)
        serializer = DishDetailSerializer(dish, context={'user': request.user})
        
        # 如果用户已认证，记录浏览历史
        if request.user.is_authenticated:
            BrowsingHistory.objects.create(user=request.user, dish=dish)
        
        return Response(serializer.data, status=status.HTTP_200_OK)
