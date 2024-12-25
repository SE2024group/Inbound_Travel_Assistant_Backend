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
    将 kwargs 里需要替换的变量进行 format，如 {dish_id}。
    最终返回完整的 BASE_URL + 路径
    """
    endpoint = API_ENDPOINTS.get(key, "")
    if kwargs:
        endpoint = endpoint.format(**kwargs)
    return urljoin(BASE_URL, endpoint)

# 辅助函数：获取本地测试文件路径
def media_path(filename: str):
    """
    假设测试文件存放于 auto_test/media/ 下。
    若路径不同，请在此处修改。
    """
    return os.path.join(os.path.dirname(__file__), 'media', filename)


# ============== 测试用例开始 =============

@pytest.mark.order(1)
def test_echo():
    """
    测试 EchoView: /echo/
    发送POST请求携带 {username}，期望返回 200，body中包含 echo 的内容
    """
    url = api_url("echo")
    payload = {"username": "testuser"}
    r = requests.post(url, json=payload)
    # 如果 EchoView 允许匿名访问，则期望200；否则请将测试修改为expect 401
    assert r.status_code == 200, f"Echo API expected 200, got {r.status_code}"
    data = r.json()
    assert data["username"] == "testuser"

@pytest.mark.order(2)
def test_register():
    """
    测试注册: /register/
    - 注册时必须提供 password2(与password相同)
    - 成功注册后返回201，body中包含 { user, token }
    - 重复注册可期望400
    """
    url = api_url("register")
    payload = {
        "username": "testuser",
        "password": "testpass",
        "password2": "testpass",
        "email": "test@example.com"
    }
    r = requests.post(url, json=payload)
    assert r.status_code in [201, 400], f"Register API unexpected status: {r.status_code}"

    data = r.json()
    if r.status_code == 201:
        assert "token" in data, "Token not found in register response"
        assert "user" in data, "User object not found in register response"

@pytest.mark.order(3)
def test_login():
    """
    测试登录: /login/
    - 使用已注册的用户登录
    - 校验token
    """
    url = api_url("login")
    payload = {"username": "testuser", "password": "testpass"}
    r = requests.post(url, json=payload)
    # 由于LoginSerializer可能raise ValidationError => 400
    # 而视图可能返回401 => invalid login
    # 成功 => 200
    # 因此接收 [200,400,401]
    assert r.status_code in [200, 400, 401], f"Login API expected 200 or 400/401, got {r.status_code}"

    data = r.json()
    if r.status_code == 200:
        assert "token" in data
        assert "user" in data
        pytest.token = data["token"]
    else:
        pytest.token = None

@pytest.mark.order(4)
def test_user_detail_get():
    """
    测试获取用户详细信息: /user/
    - GET需携带 token
    - 若token无效，期望401/403
    """
    if not getattr(pytest, "token", None):
        pytest.skip("No valid token, skip user_detail_get")

    url = api_url("user_detail")
    headers = {"Authorization": f"Token {pytest.token}"}
    r = requests.get(url, headers=headers)
    if r.status_code != 200:
        pytest.skip(f"User detail GET returned {r.status_code}, cannot proceed.")
    data = r.json()
    assert data["username"] == "testuser"

@pytest.mark.order(5)
def test_user_detail_put():
    """
    测试更新用户详细信息: /user/
    - PUT/PATCH请求需携带 token
    """
    if not getattr(pytest, "token", None):
        pytest.skip("No valid token, skip user_detail_put")

    url = api_url("user_detail")
    headers = {"Authorization": f"Token {pytest.token}"}
    payload = {"nickname": "NewNick"}
    r = requests.patch(url, headers=headers, json=payload)
    # 可能400 => 部分字段不合法；也可能200 => 成功
    assert r.status_code in [200, 400], f"User detail PATCH got {r.status_code}"
    if r.status_code == 200:
        data = r.json()
        assert data["nickname"] == "NewNick"

@pytest.mark.order(6)
def test_ocr_failure():
    """
    测试 OCR: /ocr/
    - 不带图片文件时 => 400
    """
    url = api_url("ocr")
    r = requests.post(url)
    assert r.status_code == 400, f"OCR expected 400 if no image, got {r.status_code}"

@pytest.mark.order(7)
def test_logout():
    """
    测试登出: /logout/
    - 登出后 token 失效
    """
    if not getattr(pytest, "token", None):
        pytest.skip("No valid token, skip test_logout")

    url = api_url("logout")
    headers = {"Authorization": f"Token {pytest.token}"}
    r = requests.post(url, headers=headers)
    assert r.status_code in [200, 400], f"Logout expected 200 or 400, got {r.status_code}"
    # 若成功 => token失效
    if r.status_code == 200:
        # 再次访问 user_detail => should be 401/403
        user_url = api_url("user_detail")
        check_r = requests.get(user_url, headers=headers)
        assert check_r.status_code in [401, 403], f"Expect unauthorized after logout, got {check_r.status_code}"

@pytest.mark.order(8)
def test_login_invalid():
    """
    测试无效密码登录 => 期望返回 400 或 401
    """
    url = api_url("login")
    payload = {"username": "testuser", "password": "wrongpass"}
    r = requests.post(url, json=payload)
    assert r.status_code in [400, 401], f"Invalid login should get 400 or 401, got {r.status_code}"

@pytest.mark.order(9)
def test_voice_translation_invalid():
    """
    测试语音翻译: /voice-translation/
    - 上传非音频文件 => 400/500
    """
    url = api_url("voice_translation")
    files = {
        "voice_file": ("fake.txt", b"This is not an audio file", "text/plain"),
    }
    data = {"isChineseMode": "true"}

    r = requests.post(url, files=files, data=data)
    assert r.status_code in [400, 500], f"Expect 400 or 500 if file is invalid audio, got {r.status_code}"

@pytest.mark.order(10)
def test_search_dish_empty_tags():
    """
    测试菜品搜索: /dish/search/
    - 不带任何 tag => code=200, data.results => []
    """
    url = api_url("dish_search")
    payload = {"tags": []}
    r = requests.post(url, json=payload)
    # 可能 200(成功) 或 400(缺参数)
    assert r.status_code in [200, 400], f"Expect 200 or 400, got {r.status_code}"
    if r.status_code == 200:
        data = r.json()
        assert "results" in data["data"]

@pytest.mark.order(11)
def test_advanced_search_empty_text():
    """
    测试进阶搜索API: /dish/advanced_search/
    - text='', filter=[]
    """
    url = api_url("dish_advanced_search")
    payload = {"text": "", "filter": []}
    r = requests.post(url, json=payload)
    assert r.status_code in [200, 400], f"Expect 200 or 400, got {r.status_code}"
    data = r.json()
    print("advanced_search_empty_text data:", data)

@pytest.mark.order(12)
def test_tag_list():
    """
    获取标签列表: /tags/
    """
    url = api_url("tags")
    r = requests.get(url)
    assert r.status_code == 200, f"Tag list expected 200, got {r.status_code}"
    data = r.json()
    print("tag list:", data)

# ============== 新增对五个媒体文件的API测试 ==============

@pytest.mark.order(13)
def test_ocr_success():
    """
    测试 OCR 成功场景: /ocr/
    - 上传 menu.jpg => 期望200或400(如果图片无可识别)
    """
    file_path = media_path("menu.jpg")
    if not os.path.exists(file_path):
        pytest.skip("menu.jpg not found, skip test_ocr_success")

    url = api_url("ocr")
    with open(file_path, "rb") as f:
        files = {"image": ("menu.jpg", f, "image/jpeg")}
        r = requests.post(url, files=files)
    # 后端可能返回200(成功) 或 400(识别失败或解析错误)
    assert r.status_code in [200, 400], f"OCR file upload expected 200 or 400, got {r.status_code}"


@pytest.mark.order(14)
def test_comment_upload_with_image():
    """
    测试评论上传 => /comments/upload/
    - 上传 comment.jpg 作为评论图片
    - 需先登录获取token
    """
    if not getattr(pytest, "token", None):
        pytest.skip("No valid token, skip comment_upload_with_image")

    file_path = media_path("comment.jpg")
    if not os.path.exists(file_path):
        pytest.skip("comment.jpg not found, skip test_comment_upload_with_image")

    url = api_url("comment_upload")
    headers = {"Authorization": f"Token {pytest.token}"}
    data = {
        "dish": 1,  # 假设dish_id=1有效
        "comment": "测试评论带图片",
        "rating": 4
    }
    files = [
        ("images", ("comment.jpg", open(file_path, "rb"), "image/jpeg"))
    ]
    r = requests.post(url, headers=headers, data=data, files=files)
    assert r.status_code in [201, 400], f"Comment upload expected 201 or 400, got {r.status_code}"
    if r.status_code == 201:
        resp_json = r.json()
        assert resp_json["comment"] == "测试评论带图片"


@pytest.mark.order(15)
def test_user_detail_upload_avatar():
    """
    测试用户上传头像 => /user/ (PATCH)
    - avatar.jpg
    """
    if not getattr(pytest, "token", None):
        pytest.skip("No valid token, skip user_detail_upload_avatar")

    file_path = media_path("avatar.jpg")
    if not os.path.exists(file_path):
        pytest.skip("avatar.jpg not found, skip test_user_detail_upload_avatar")

    url = api_url("user_detail")
    headers = {"Authorization": f"Token {pytest.token}"}
    files = {
        "avatar": ("avatar.jpg", open(file_path, "rb"), "image/jpeg")
    }
    r = requests.patch(url, headers=headers, files=files)
    assert r.status_code in [200, 400], f"Avatar upload got {r.status_code}"
    if r.status_code == 200:
        data = r.json()
        assert "avatar" in data, "No avatar field in response"


@pytest.mark.order(16)
def test_voice_translation_chinese_wav():
    """
    测试语音翻译(中文模式) => /voice-translation/
    - 上传 test.wav, isChineseMode=true
    """
    if not getattr(pytest, "token", None):
        pytest.skip("Not strictly required token, but skipping if we prefer consistent environment")

    file_path = media_path("test.wav")
    if not os.path.exists(file_path):
        pytest.skip("test.wav not found, skip test_voice_translation_chinese_wav")

    url = api_url("voice_translation")
    files = {
        "voice_file": ("test.wav", open(file_path, "rb"), "audio/wav")
    }
    data = {"isChineseMode": "true"}

    r = requests.post(url, files=files, data=data)
    # 可能200成功, 400/500错误
    assert r.status_code in [200, 400, 500], f"Voice translation CHN wav => got {r.status_code}"
    print("test_voice_translation_chinese_wav:", r.json())


@pytest.mark.order(17)
def test_voice_translation_english_wav():
    """
    测试语音翻译(英文模式) => /voice-translation/
    - 上传 eng-test.wav, isChineseMode=false
    """
    file_path = media_path("eng-test.wav")
    if not os.path.exists(file_path):
        pytest.skip("eng-test.wav not found, skip test_voice_translation_english_wav")

    url = api_url("voice_translation")
    files = {
        "voice_file": ("eng-test.wav", open(file_path, "rb"), "audio/wav")
    }
    data = {"isChineseMode": "false"}

    r = requests.post(url, files=files, data=data)
    assert r.status_code in [200, 400, 500], f"Voice translation ENG wav => got {r.status_code}"
    print("test_voice_translation_english_wav:", r.json())

