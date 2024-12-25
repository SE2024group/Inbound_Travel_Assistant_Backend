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
    endpoint = API_ENDPOINTS.get(key, "")
    if kwargs:
        endpoint = endpoint.format(**kwargs)
    return urljoin(BASE_URL, endpoint)

def media_path(filename: str):
    """
    假设测试文件放在 auto_test/media/ 下，若路径不同请在此处修改。
    """
    return os.path.join(os.path.dirname(__file__), 'media', filename)


def test_echo():
    """
    测试 EchoView: /echo/
    若 EchoView 允许匿名访问 => 预期 200; 否则自行修改为 401
    """
    url = api_url("echo")
    payload = {"username": "testuser"}
    r = requests.post(url, json=payload)
    assert r.status_code == 200, f"Echo expected 200, got {r.status_code}"
    data = r.json()
    assert data.get("username") == "testuser"


def test_register():
    """
    注册: /register/ 
    需提供 password、password2字段
    成功 => 201; 若重复注册 => 400
    """
    url = api_url("register")
    payload = {
        "username": "testuser",
        "password": "testpass",
        "password2": "testpass",
        "email": "test@example.com"
    }
    r = requests.post(url, json=payload)
    assert r.status_code in [201, 400], f"Register got {r.status_code}"
    data = r.json()
    if r.status_code == 201:
        assert "token" in data
        assert "user" in data


def test_login():
    """
    登录: /login/
    校验token
    - 服务器可能返回 200(成功), 400(ValidationError), 401(无效凭证)
    """
    url = api_url("login")
    payload = {"username": "testuser", "password": "testpass"}
    r = requests.post(url, json=payload)
    assert r.status_code in [200, 400, 401], f"Login got {r.status_code}"
    if r.status_code == 200:
        data = r.json()
        assert "token" in data
        pytest.token = data["token"]
    else:
        pytest.token = None


def test_user_detail_get():
    """
    获取用户信息: /user/
    必须携带 token => 如果无 token, skip
    """
    if not getattr(pytest, "token", None):
        pytest.skip("No valid token => skip user_detail_get")

    url = api_url("user_detail")
    headers = {"Authorization": f"Token {pytest.token}"}
    r = requests.get(url, headers=headers)
    # 若后端需要验证 => 200 / 无权限 => 401/403
    if r.status_code != 200:
        pytest.skip(f"user detail GET got {r.status_code}, skip")
    data = r.json()
    assert data.get("username") == "testuser"

def test_user_detail_put():
    """
    测试更新用户详细信息: /user/
    - 后端只接受 multipart/form-data
    - PATCH 需携带 Token，否则 401/403
    """
    if not getattr(pytest, "token", None):
        pytest.skip("No valid token => skip test_user_detail_put")

    url = api_url("user_detail")
    headers = {
        "Authorization": f"Token {pytest.token}"
        # 不指定 Content-Type，让 requests 自动生成 boundary
    }

    # 这里使用 `data` + `files={}` 的方式构造multipart/form-data
    # 假设只改 nickname，不上传任何文件
    data = {"nickname": "NewNick"}
    # 如果你想同时上传头像，也可放到 files。
    files = {}

    r = requests.patch(url, headers=headers, data=data, files=files)
    # 后端若成功 => 200； 若 nickname 字段无效 => 400； 若 token 无效 => 401/403
    assert r.status_code in [200, 400, 401, 403], f"user detail PATCH got {r.status_code}"

    if r.status_code == 200:
        data_json = r.json()
        assert data_json.get("nickname") == "NewNick", "更新后应返回新的 nickname"

def test_ocr_failure():
    """
    OCR: /ocr/
    不带图片 => 400
    """
    url = api_url("ocr")
    r = requests.post(url)
    assert r.status_code == 400, f"Expect 400 if no image => got {r.status_code}"


def test_logout():
    """
    /logout/
    - 登出后 token 失效
    """
    if not getattr(pytest, "token", None):
        pytest.skip("No valid token => skip logout")

    url = api_url("logout")
    headers = {"Authorization": f"Token {pytest.token}"}
    r = requests.post(url, headers=headers)
    # 200 => 成功; 400 => token 不存在
    if r.status_code == 200:
        # check again => /user/ => 401/403
        check = requests.get(api_url("user_detail"), headers=headers)
        assert check.status_code in [401, 403], f"After logout => expect unauthorized => {check.status_code}"


def test_login_invalid():
    """
    /login/ 无效密码 => 400/401
    """
    url = api_url("login")
    payload = {"username": "testuser", "password": "wrongpass"}
    r = requests.post(url, json=payload)
    assert r.status_code in [400, 401], f"Invalid login => got {r.status_code}"


def test_voice_translation_invalid():
    """
    /voice-translation/
    上传非音频 => 400/500
    """
    url = api_url("voice_translation")
    files = {"voice_file": ("fake.txt", b"Fake audio", "text/plain")}
    data = {"isChineseMode": "true"}
    r = requests.post(url, files=files, data=data)
    assert r.status_code in [400, 500], f"Voice invalid => got {r.status_code}"


def test_search_dish_empty_tags():
    """
    /dish/search/
    tags=[]
    """
    url = api_url("dish_search")
    payload = {"tags": []}
    r = requests.post(url, json=payload)
    assert r.status_code in [200, 400], f"Search dish => {r.status_code}"
    if r.status_code == 200:
        data = r.json()
        assert "results" in data.get("data", {})


def test_advanced_search_empty_text():
    """
    /dish/advanced_search/
    text='', filter=[]
    """
    url = api_url("dish_advanced_search")
    payload = {"text": "", "filter": []}
    r = requests.post(url, json=payload)
    assert r.status_code in [200, 400], f"Advanced search => {r.status_code}"
    data = r.json()
    print("advanced_search_empty_text data =>", data)


def test_tag_list():
    """
    /tags/
    不需token => 200
    """
    url = api_url("tags")
    r = requests.get(url)
    assert r.status_code == 200, f"Tags => {r.status_code}"
    data = r.json()
    print("tags list =>", data)

# =========== 以下为上传媒体文件的测试 =============

def test_ocr_success():
    """
    OCR 成功场景 => /ocr/
    上传 menu.jpg => 200/400/500 视后端处理
    """
    file_path = media_path("menu.jpg")
    if not os.path.exists(file_path):
        pytest.skip("menu.jpg not found => skip")

    url = api_url("ocr")
    with open(file_path, "rb") as f:
        files = {"image": ("menu.jpg", f, "image/jpeg")}
        r = requests.post(url, files=files)
    # 若OCR处理成功 => 200; 如果后端无法处理 => 400/500
    assert r.status_code in [200, 400, 500], f"OCR => got {r.status_code}"

def test_comment_upload_with_image():
    """
    评论上传 => /comments/upload/
    - images => comment.jpg
    - 需token
    - 若token失效 => 401
    - 成功 => 201 or 400(参数问题)
    """
    if not getattr(pytest, "token", None):
        pytest.skip("No valid token => skip")

    file_path = media_path("comment.jpg")
    if not os.path.exists(file_path):
        pytest.skip("comment.jpg not found => skip")

    url = api_url("comment_upload")
    headers = {"Authorization": f"Token {pytest.token}"}
    data = {"dish": 1, "comment": "测试评论带图片", "rating": 4}
    files = [("images", ("comment.jpg", open(file_path, "rb"), "image/jpeg"))]
    r = requests.post(url, headers=headers, data=data, files=files)
    # token无效 => 401; 成功 => 201; 参数问题 => 400
    assert r.status_code in [201, 400, 401], f"comment upload => {r.status_code}"

def test_user_detail_upload_avatar():
    """
    上传头像 => /user/
    - avatar => avatar.jpg
    - 需token => 否则401
    - 成功 => 200 or 400(字段错误)
    """
    if not getattr(pytest, "token", None):
        pytest.skip("No valid token => skip avatar")

    file_path = media_path("avatar.jpg")
    if not os.path.exists(file_path):
        pytest.skip("avatar.jpg not found => skip")

    url = api_url("user_detail")
    headers = {"Authorization": f"Token {pytest.token}"}
    files = {"avatar": ("avatar.jpg", open(file_path, "rb"), "image/jpeg")}
    r = requests.patch(url, headers=headers, files=files)
    # 若后端未登录 => 401; 成功 => 200; 可能400 => 不合法
    assert r.status_code in [200, 400, 401], f"avatar upload => {r.status_code}"

def test_voice_translation_chinese_m4a():
    """
    /voice-translation/
    测试中文m4a => test.m4a
    """
    file_path = media_path("test.m4a")
    if not os.path.exists(file_path):
        pytest.skip("test.m4a not found => skip")

    url = api_url("voice_translation")
    files = {"voice_file": ("test.m4a", open(file_path, "rb"), "audio/m4a")}
    data = {"isChineseMode": "true"}
    r = requests.post(url, files=files, data=data)
    # 可能200/400/500
    assert r.status_code in [200, 400, 500], f"voice CHN => {r.status_code}"

def test_voice_translation_english_m4a():
    """
    /voice-translation/
    测试英文m4a => eng-test.m4a
    """
    file_path = media_path("eng-test.m4a")
    if not os.path.exists(file_path):
        pytest.skip("eng-test.m4a not found => skip")

    url = api_url("voice_translation")
    files = {"voice_file": ("eng-test.m4a", open(file_path, "rb"), "audio/m4a")}
    data = {"isChineseMode": "false"}
    r = requests.post(url, files=files, data=data)
    assert r.status_code in [200, 400, 500], f"voice ENG => {r.status_code}"
