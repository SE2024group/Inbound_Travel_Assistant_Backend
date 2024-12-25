# tests/test_utils.py

import os
import pytest
from unittest.mock import patch, MagicMock
from app.utils import ocr_process_image, translate_text

@pytest.mark.django_db
def test_ocr_process_image():
    """
    测试 OCR 工具函数:
    - 传入示例图片或使用 mock 来模拟第三方OCR API返回
    """
    # 方案A：如果 ocr_process_image 内部调用外部API，用 mock.patch 替代网络请求
    mock_response = {"text": "测试文字"}
    with patch("app.utils.requests.post") as mock_post:
        mock_post.return_value.ok = True
        mock_post.return_value.json.return_value = mock_response

        result = ocr_process_image("tests/media/sample.png")  # 示例图片地址
        assert "测试文字" in result, "OCR结果应包含  '测试文字'"

@pytest.mark.parametrize("input_text, from_lang, to_lang, expected_output", [
    ("你好，世界", "ZH", "EN", "Hello, world"),
    ("Hello, world", "EN", "ZH", "你好，世界"),
])
def test_translate_text(input_text, from_lang, to_lang, expected_output):
    """
    测试文本翻译函数:
    - 使用不同语言参数检查翻译结果
    """
    # 同理可用 mock 来模拟第三方翻译API调用
    with patch("app.utils.requests.post") as mock_post:
        # 假设第三方API返回的json结构
        mock_post.return_value.ok = True
        mock_post.return_value.json.return_value = {
            "data": {"dst": expected_output},
            "code": 0
        }

        output = translate_text(input_text, from_lang, to_lang)
        assert expected_output == output, f"翻译结果应为 {expected_output}, 实际为 {output}"
