from django.test import TestCase
# web/api/tests.py

from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from .models import Tag
from unittest.mock import patch

User = get_user_model()


class UserAPITests(APITestCase):

    def setUp(self):
        """
        在每个测试方法运行前执行，用于创建测试数据和配置测试环境。
        """
        # 创建一些 Tag 实例用于测试饮食禁忌
        self.tag1 = Tag.objects.create(name="Vegetarian")
        self.tag2 = Tag.objects.create(name="Gluten-Free")
        self.tag3 = Tag.objects.create(name="Halal")
        self.tag4 = Tag.objects.create(name="Vegan")

        # 注册 URL
        self.register_url = reverse('register')
        # 登录 URL
        self.login_url = reverse('login')
        # 更新用户偏好 URL
        self.update_preferences_url = reverse('user-preferences')
        # 文字翻译 URL
        self.text_translation_url = reverse('text-translation')
        # 登出 URL
        self.logout_url = reverse('logout')

    def authenticate(self):
        """
        辅助方法，用于注册并登录一个用户，返回 Token。
        """
        user = User.objects.create_user(username='john_doe', password='securepassword123')
        data = {
            "username": "john_doe",
            "password": "securepassword123"
        }
        response = self.client.post(self.login_url, data, format='json')
        token = response.data['token']
        return token

    # 用户注册测试
    def test_user_registration_success(self):
        """
        确保用户可以成功注册。
        """
        data = {
            "username": "jane_doe",
            "password": "securepassword123",
            "password2": "securepassword123"
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['username'], 'jane_doe')
        self.assertIsNotNone(response.data['user']['signup_date'])
        self.assertEqual(response.data['user']['religious_belief'], None)
        self.assertListEqual(response.data['user']['dietary_restrictions'], [])

    def test_user_registration_password_mismatch(self):
        """
        确保注册失败当密码和确认密码不匹配时。
        """
        data = {
            "username": "jane_doe",
            "password": "securepassword123",
            "password2": "differentpassword"
        }
        response = self.client.post(self.register_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password2', response.data)

    # 用户登录测试
    def test_user_login_success(self):
        """
        确保用户可以成功登录并获取 Token。
        """
        # 先注册一个用户
        user = User.objects.create_user(username='john_doe', password='securepassword123')

        data = {
            "username": "john_doe",
            "password": "securepassword123"
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)
        self.assertIn('user', response.data)
        self.assertEqual(response.data['user']['username'], 'john_doe')

    def test_user_login_invalid_credentials(self):
        """
        确保登录失败当凭证无效时。
        """
        # 尝试登录一个不存在的用户
        data = {
            "username": "nonexistent_user",
            "password": "somepassword"
        }
        response = self.client.post(self.login_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], "Invalid username or password.")

    # 更新用户偏好测试
    def test_update_user_preferences_success(self):
        """
        确保已认证用户可以成功更新偏好。
        """
        token = self.authenticate()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)

        data = {
            "religious_belief": "Islam",
            "dietary_restrictions": ["Halal", "Vegan"]
        }
        response = self.client.patch(self.update_preferences_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], "Preferences updated successfully.")
        self.assertEqual(response.data['user']['religious_belief'], "Islam")
        self.assertListEqual(response.data['user']['dietary_restrictions'], ["Halal", "Vegan"])

    def test_update_user_preferences_invalid_data(self):
        """
        确保更新失败当提供无效数据时。
        """
        token = self.authenticate()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)

        data = {
            "dietary_restrictions": "Not a list"  # 应该是列表
        }
        response = self.client.patch(self.update_preferences_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)

    def test_update_user_preferences_unauthenticated(self):
        """
        确保更新失败当用户未认证时。
        """
        data = {
            "religious_belief": "Buddhism",
            "dietary_restrictions": ["Vegetarian"]
        }
        response = self.client.patch(self.update_preferences_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # 文字翻译测试
    @patch('api.utils.translate_text')
    def test_text_translation_chinese_to_english_success(self, mock_translate):
        """
        确保成功将中文翻译为英文。
        """
        # 模拟 translate_text 的返回值
        mock_translate.return_value = "Hello world"

        data = {
            "text": "你好世界",
            "isChineseMode": True
        }
        response = self.client.post(self.text_translation_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], 200)
        self.assertEqual(response.data['message'], "上传成功")
        self.assertEqual(response.data['data']['cn_text'], "你好世界")
        self.assertEqual(response.data['data']['en_text'], "Hello world")
        self.assertTrue(response.data['data']['isChineseMode'])
        mock_translate.assert_called_once_with("你好世界", from_lang="ZH", to_lang="EN")

    @patch('api.utils.translate_text')
    def test_text_translation_english_to_chinese_success(self, mock_translate):
        """
        确保成功将英文翻译为中文。
        """
        mock_translate.return_value = "你好世界"

        data = {
            "text": "Hello world",
            "isChineseMode": False
        }
        response = self.client.post(self.text_translation_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['code'], 200)
        self.assertEqual(response.data['message'], "上传成功")
        self.assertEqual(response.data['data']['en_text'], "Hello world")
        self.assertEqual(response.data['data']['cn_text'], "你好世界")
        self.assertFalse(response.data['data']['isChineseMode'])
        mock_translate.assert_called_once_with("Hello world", from_lang="EN", to_lang="ZH")

    def test_text_translation_invalid_data(self):
        """
        确保翻译失败当提供无效数据时。
        """
        data = {
            "text": "",
            "isChineseMode": "not_a_boolean"
        }
        response = self.client.post(self.text_translation_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('errors', response.data)

    @patch('api.utils.translate_text')
    def test_text_translation_server_error(self, mock_translate):
        """
        确保在翻译过程中发生服务器错误时返回 500。
        """
        mock_translate.side_effect = Exception("Translation API failed")

        data = {
            "text": "Hello world",
            "isChineseMode": False
        }
        response = self.client.post(self.text_translation_url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertEqual(response.data['code'], 500)
        self.assertEqual(response.data['message'], "服务器内部错误")
        self.assertEqual(response.data['errors'], "Translation API failed")

    # 用户登出测试
    def test_user_logout_success(self):
        """
        确保已认证用户可以成功登出。
        """
        token = self.authenticate()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + token)

        response = self.client.post(self.logout_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], "Logged out successfully.")

        # 确认 Token 已删除
        with self.assertRaises(User.auth_token.RelatedObjectDoesNotExist):
            User.objects.get(username='john_doe').auth_token

    def test_user_logout_invalid_token(self):
        """
        确保登出失败当 Token 无效时。
        """
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + 'invalidtoken123')
        response = self.client.post(self.logout_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('error', response.data)
        self.assertEqual(response.data['error'], "Token not found.")

    def test_user_logout_unauthenticated(self):
        """
        确保登出失败当用户未认证时。
        """
        response = self.client.post(self.logout_url, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
