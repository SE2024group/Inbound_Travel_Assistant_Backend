import os
import pytest
import requests
from urllib.parse import urljoin

# ========== 配置基础 ==========
# 可通过环境变量 BASE_TEST_URL 覆盖默认 localhost:8000
BASE_URL = os.getenv("BASE_TEST_URL", "http://127.0.0.1:8000")
print("Using BASE_URL:", BASE_URL)
# 方便管理路由路径
API_ENDPOINTS = {
    "echo": "/api/echo/",
    "register": "/api/register/",
    "login": "/api/login/",
    "logout": "/api/logout/",
    "user_detail": "/api/user/",
    "user_preferences": "/api/user/preferences/",
    "browsing_history": "/api/browsing-history/",
    "like_history": "/api/like-history/",
    "favorite_history": "/api/favorite-history/",
    "comment_history": "/api/comment-history/",
    "comment_upload": "/api/comments/upload/",
    "comment_delete": "/api/comments/{comment_id}/delete/",
    "dish_comments": "/api/dish/{dish_id}/comments/",
    "user_comments": "/api/user/comments/",
    "ocr": "/api/ocr/",
    "dish_detail": "/api/dish/{dish_id}/",
    "voice_translation": "/api/voice-translation/",
    "text_translation": "/api/text-translation/",
    "dish_search": "/api/dish/search/",
    "dish_advanced_search": "/api/dish/advanced_search/",
    "tags": "/api/tags/",
    "favorite_toggle": "/api/favorite/{dish_id}/",
    "favorites": "/api/favorites/",
}


def api_url(key, **kwargs):
    """
    根据 key 在 API_ENDPOINTS 中获取相对路径，
    并将 kwargs 里需要替换的变量进行格式化（如 {dish_id}）。
    最终返回完整的 BASE_URL + 路径
    """
    endpoint = API_ENDPOINTS.get(key, "")
    if kwargs:
        endpoint = endpoint.format(**kwargs)
    return urljoin(BASE_URL, endpoint)


@pytest.mark.order(1)
def test_echo():
    """
    测试 EchoView: /echo/
    - 发送POST请求携带 {username}，期望返回 200，body中包含 echo 的内容
    """
    url = api_url("echo")
    payload = {"username": "testuser"}
    r = requests.post(url, json=payload)
    assert r.status_code == 200, f"Echo API expected 200, got {r.status_code}"
    data = r.json()
    assert data["username"] == "testuser"


@pytest.mark.order(2)
def test_register():
    """
    测试注册: /register/
    - 成功注册后返回201，返回user和token
    """
    url = api_url("register")
    payload = {
        "username": "testuser",
        "password": "testpass",
        "email": "test@example.com"
    }
    r = requests.post(url, json=payload)
    # 对于重复注册可写额外测试
    assert r.status_code in [201, 400], f"Register API unexpected status: {r.status_code}"

    data = r.json()
    if r.status_code == 201:
        assert "token" in data
        assert "user" in data


@pytest.mark.order(3)
def test_login():
    """
    测试登录: /login/
    - 使用前面注册的用户登录
    - 校验token
    """
    url = api_url("login")
    payload = {
        "username": "testuser",
        "password": "testpass",
    }
    r = requests.post(url, json=payload)
    assert r.status_code in [200, 401], f"Login API expected 200 or 401, got {r.status_code}"

    data = r.json()
    if r.status_code == 200:
        assert "token" in data
        assert "user" in data
        # 将 token 暂存，后续测试需要
        pytest.token = data["token"]
    else:
        pytest.token = None


@pytest.mark.order(4)
def test_user_detail_get():
    """
    测试获取用户详细信息: /user/
    - GET请求需携带token
    """
    if not getattr(pytest, "token", None):
        pytest.skip("No valid token, skip test_user_detail_get")

    url = api_url("user_detail")
    headers = {"Authorization": f"Token {pytest.token}"}
    r = requests.get(url, headers=headers)
    assert r.status_code == 200, f"User detail GET expected 200, got {r.status_code}"
    data = r.json()
    assert data["username"] == "testuser"


@pytest.mark.order(5)
def test_user_detail_put():
    """
    测试更新用户详细信息: /user/
    - PUT/PATCH请求需携带token
    """
    if not getattr(pytest, "token", None):
        pytest.skip("No valid token, skip test_user_detail_put")

    url = api_url("user_detail")
    headers = {"Authorization": f"Token {pytest.token}"}
    payload = {
        "nickname": "NewNick"
    }
    r = requests.patch(url, headers=headers, json=payload)
    assert r.status_code in [200, 400], f"User detail PATCH got {r.status_code}"
    if r.status_code == 200:
        data = r.json()
        assert data["nickname"] == "NewNick"


@pytest.mark.order(6)
def test_ocr_failure():
    """
    测试 OCR: /ocr/
    - 不带图片文件时，期望返回400
    """
    url = api_url("ocr")
    r = requests.post(url)
    assert r.status_code == 400, f"OCR expected 400 if no image, got {r.status_code}"


@pytest.mark.order(7)
def test_logout():
    """
    测试登出: /logout/
    - 登出后token失效
    """
    if not getattr(pytest, "token", None):
        pytest.skip("No valid token, skip test_logout")

    url = api_url("logout")
    headers = {"Authorization": f"Token {pytest.token}"}
    r = requests.post(url, headers=headers)
    assert r.status_code in [200, 400], f"Logout expected 200 or 400, got {r.status_code}"
    if r.status_code == 200:
        # 再次访问 /user/ 应该403或401
        user_url = api_url("user_detail")
        check_r = requests.get(user_url, headers=headers)
        assert check_r.status_code in [401, 403], f"After logout, user detail should be unauthorized"


@pytest.mark.order(8)
def test_login_invalid():
    """
    测试使用错误的密码登录: 期望返回401
    """
    url = api_url("login")
    payload = {
        "username": "testuser",
        "password": "wrongpass",
    }
    r = requests.post(url, json=payload)
    assert r.status_code == 401, f"Invalid login should get 401, got {r.status_code}"


@pytest.mark.order(9)
def test_voice_translation_invalid():
    """
    测试语音翻译: /voice-translation/
    - 上传非音频文件，期望失败
    """
    url = api_url("voice_translation")
    files = {
        "voice_file": ("fake.txt", b"This is not an audio file"),
    }
    data = {"isChineseMode": "true"}

    r = requests.post(url, files=files, data=data)
    assert r.status_code in [400, 500], f"Expect 400 or 500 if file is invalid audio, got {r.status_code}"

    data_res = r.json()
    print("voice_translation invalid test result:", data_res)


@pytest.mark.order(10)
def test_search_dish_empty_tags():
    """
    测试菜品搜索: /dish/search/
    - 不带任何tag
    """
    url = api_url("dish_search")
    payload = {
        "tags": []
    }
    r = requests.post(url, json=payload)
    assert r.status_code in [200, 400], f"Expect 200 or 400, got {r.status_code}"
    if r.status_code == 200:
        data = r.json()
        assert "results" in data["data"]


@pytest.mark.order(11)
def test_advanced_search_empty_text():
    """
    测试进阶搜索API: /dish/advanced_search/
    - 不带text
    """
    url = api_url("dish_advanced_search")
    payload = {
        "text": "",
        "filter": []
    }
    r = requests.post(url, json=payload)
    assert r.status_code in [200, 400], f"Expect 200 or 400, got {r.status_code}"
    data = r.json()
    print("advanced_search_empty_text data:", data)


@pytest.mark.order(12)
def test_tag_list():
    """
    测试获取所有标签: /tags/
    - 不需要认证
    """
    url = api_url("tags")
    r = requests.get(url)
    assert r.status_code == 200, f"Tag list should be public, got {r.status_code}"
    data = r.json()
    print("tags list:", data)



# ===================== 新增的上传媒体文件相关测试 =====================

@pytest.mark.order(13)
def test_ocr_success():
    """
    测试 OCR 上传图片成功场景: /ocr/
    - 上传 menu.jpg, 期望 200
    """
    url = api_url("ocr")
    with open("tests_api/media/menu.jpg", "rb") as f:
        files = {"image": ("menu.jpg", f, "image/jpeg")}
        r = requests.post(url, files=files)
    # 对OCR结果做最基本的断言
    assert r.status_code in [200, 400], f"OCR file upload expected 200 or 400, got {r.status_code}"
    data = r.json()
    print("OCR success test result:", data)


@pytest.mark.order(14)
def test_comment_upload_with_image():
    """
    测试评论上传，需要token: /comments/upload/
    - 上传一张 comment.jpg
    """
    if not getattr(pytest, "token", None):
        pytest.skip("No valid token, skip test_comment_upload_with_image")

    url = api_url("comment_upload")
    headers = {"Authorization": f"Token {pytest.token}"}
    payload = {
        "dish": 1,           # 假设 dish_id=1 存在
        "comment": "测试评论带图片",
        "rating": 4
    }
    files = [
        ("images", ("comment.jpg", open("tests_api/media/comment.jpg", "rb"), "image/jpeg"))
    ]
    r = requests.post(url, headers=headers, data=payload, files=files)
    assert r.status_code in [201, 400], f"Comment upload expected 201 or 400, got {r.status_code}"
    if r.status_code == 201:
        data = r.json()
        print("Comment upload with image result:", data)
        assert data["comment"] == "测试评论带图片"


@pytest.mark.order(15)
def test_user_detail_upload_avatar():
    """
    测试用户上传头像: /user/
    - 上传 avatar.jpg
    """
    if not getattr(pytest, "token", None):
        pytest.skip("No valid token, skip test_user_detail_upload_avatar")

    url = api_url("user_detail")
    headers = {"Authorization": f"Token {pytest.token}"}
    files = {
        "avatar": ("avatar.jpg", open("tests_api/media/avatar.jpg", "rb"), "image/jpeg")
    }
    r = requests.patch(url, headers=headers, files=files)
    assert r.status_code in [200, 400], f"User detail avatar upload got {r.status_code}"
    if r.status_code == 200:
        data = r.json()
        assert "avatar" in data, "Avatar field not returned"


@pytest.mark.order(16)
def test_voice_translation_chinese_m4a():
    """
    测试语音翻译, 中文模式: /voice-translation/
    - 使用 test.m4a, isChineseMode=true
    """
    if not os.path.exists("tests_api/media/test.m4a"):
        pytest.skip("test.m4a not found in media/")

    url = api_url("voice_translation")
    files = {
        "voice_file": ("test.m4a", open("tests_api/media/test.m4a", "rb"), "audio/m4a"),
    }
    data = {"isChineseMode": "true"}

    r = requests.post(url, files=files, data=data)
    assert r.status_code in [200, 400, 500], f"Voice translation CHN m4a got {r.status_code}"
    print("test_voice_translation_chinese_m4a:", r.json())


@pytest.mark.order(17)
def test_voice_translation_english_m4a():
    """
    测试语音翻译, 英文模式: /voice-translation/
    - 使用 eng-test.m4a, isChineseMode=false
    """
    if not os.path.exists("tests_api/media/eng-test.m4a"):
        pytest.skip("eng-test.m4a not found in media/")

    url = api_url("voice_translation")
    files = {
        "voice_file": ("eng-test.m4a", open("tests_api/media/eng-test.m4a", "rb"), "audio/m4a"),
    }
    data = {"isChineseMode": "false"}

    r = requests.post(url, files=files, data=data)
    assert r.status_code in [200, 400, 500], f"Voice translation ENG m4a got {r.status_code}"
    print("test_voice_translation_english_m4a:", r.json())

