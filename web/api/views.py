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

            # # 将 base64 编码的图像转换为 PNG 格式并保存在本地
            # image_data = base64.b64decode(base64_image)
            # image = Image.open(io.BytesIO(image_data))
            # image_path = os.path.join('./', f'{uuid.uuid4()}.png')
            # image.save(image_path)

            # 获取图片的 MIME 类型
            content_type = image.content_type  # e.g., 'image/jpeg'
            print(content_type)

            
            # 调用 OCR API
            ocr_api_url = 'https://api.ocr.space/parse/image'
            api_key = settings.OCR_API_KEY

            payload = {
                'language': 'chs',  # 中文简体
                'isOverlayRequired': 'true',  # 请求包含文字位置信息
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

            # 构造新的响应数据包
            result_data = []
            parsed_results = ocr_result.get('ParsedResults', [])
            for result in parsed_results:
                text_overlay = result.get('TextOverlay', {})
                lines = text_overlay.get('Lines', [])

                for line in lines:
                    line_text = line.get('LineText', '')
                    # 过滤 LineText 长度 < 3 或 > 8 的行, 以及linetext中有非汉字的行
                    if 3 <= len(line_text) <= 8 and all('\u4e00' <= char <= '\u9fff' for char in line_text):
                        words = line.get('Words', [])
                        if words:
                            # 计算 bounding_box
                            min_left = min(word['Left'] for word in words)
                            min_top = min(word['Top'] for word in words)
                            max_right = max(word['Left'] + word['Width'] for word in words)
                            max_bottom = max(word['Top'] + word['Height'] for word in words)

                            bounding_box = {
                                'top_left': {'x': min_left, 'y': min_top},
                                'bottom_right': {'x': max_right, 'y': max_bottom}
                            }

                            # 构造数据项
                            data_item = {
                                'linetext': line_text,
                                'image': 'http://1.15.174.177/static/image/.png',  # 临时图片链接
                                'ID': str(uuid.uuid4().int % 5 +1)[:1],  # 随机生成 10 位数字字符串
                                'bounding_box': bounding_box
                            }

                            result_data.append(data_item)

            # 返回新的数据包
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