# api/views.py

from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import EchoSerializer, LoginSerializer, LoginResponseSerializer, UserInfoSerializer, OCRSerializer
from django.conf import settings
from PIL import Image
import uuid
import base64
import requests
import io
import os
import random
import os
class EchoView(APIView):
    def post(self, request):
        serializer = EchoSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            return Response({'username': username}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class LoginView(APIView):
    users = {}

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            token = str(uuid.uuid4())
            # 保存用户信息（此处使用内存存储，实际应用应使用数据库）
            self.users[token] = {
                'username': username,
                'avatar': 'https://cloud.tsinghua.edu.cn/f/9d512f8861a842f38d48/?dl=1',
                'nickname': f'Nickname_{username}'
            }
            return Response({'token': token}, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

class UserInfoView(APIView):
    def get(self, request):
        auth_header = request.headers.get('Authorization')
        if not auth_header or not auth_header.startswith('Bearer '):
            return Response({'error': 'Unauthorized'}, status=status.HTTP_401_UNAUTHORIZED)

        token = auth_header.split(' ')[1]
        user = LoginView.users.get(token)
        if not user:
            return Response({'error': 'Invalid token'}, status=status.HTTP_401_UNAUTHORIZED)

        data = {
            'avatar': user['avatar'],
            'nickname': user['nickname']
        }
        serializer = UserInfoSerializer(data)
        return Response(serializer.data, status=status.HTTP_200_OK)

class OCRView(APIView):
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
                        for sub_len in range(6, 1, -1):  # 优先尝试较长的子串，也可正序尝试2到6
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
                                    # 假设 dish.images.first() 返回一道图片链接，如前面已创建数据
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
    def get(self, request, id):
        try:
            dish = Dish.objects.get(id=id)
        except Dish.DoesNotExist:
            return Response({'error': 'Dish not found'}, status=status.HTTP_404_NOT_FOUND)

        serializer = DishDetailSerializer(dish)
        return Response(serializer.data, status=status.HTTP_200_OK) 