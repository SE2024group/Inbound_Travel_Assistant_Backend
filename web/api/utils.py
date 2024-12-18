# web/api/utils.py

import requests
import uuid
from django.conf import settings
import json

def translate_text(text, from_lang, to_lang):
    """
    使用必应 (Bing) 翻译 API 将文本从 from_lang 翻译到 to_lang。

    :param text: 要翻译的文本
    :param from_lang: 原文语言类型（如 "ZH"、"EN"）
    :param to_lang: 目标语言类型（如 "EN"、"ZH"）
    :return: 翻译后的文本
    :raises: Exception 如果翻译失败或文本为空
    """

    # 如果文本为空或者仅包含空白字符，则直接报错
    if not text or not text.strip():
        raise Exception("输入文本为空，请提供有效的文本进行翻译。")

    # 您的必应翻译服务密钥和终端点（请替换为您自己的）
    key = settings.COLA_KEY
    endpoint = settings.TRANSLATE_API_URL
    location = "global"  # 如果您的服务在其他区域，请相应修改

    # 根据输入语言映射Bing支持的语言代码
    # Bing使用ISO语言码，如en、zh-Hans等
    # 以下为示例映射，可根据需要扩展
    lang_map = {
        "EN": "en",
        "ZH": "zh-Hans"
    }
    from_lang_code = lang_map.get(from_lang.upper(), from_lang.lower())
    to_lang_code = lang_map.get(to_lang.upper(), to_lang.lower())

    # 构造请求URL和参数
    path = '/translate'
    constructed_url = endpoint + path

    params = {
        'api-version': '3.0',
        'from': from_lang_code,
        'to': [to_lang_code]
    }

    headers = {
        'Ocp-Apim-Subscription-Key': key,
        'Ocp-Apim-Subscription-Region': location,
        'Content-type': 'application/json',
        'X-ClientTraceId': str(uuid.uuid4())
    }

    body = [{
        'text': text
    }]

    # 发送请求
    response = requests.post(constructed_url, params=params, headers=headers, json=body)

    # 检查状态码
    if response.status_code != 200:
        raise Exception(f"翻译 API 请求失败，状态码：{response.status_code}, 响应内容：{response.text}")

    data = response.json()

    # data示例结构:
    # [
    #   {
    #     "translations": [
    #       {
    #         "text": "translated text",
    #         "to": "zh-Hans"
    #       }
    #     ]
    #   }
    # ]
    if not data or not isinstance(data, list):
        raise Exception("翻译 API 返回的数据格式不正确。")

    # 获取第一个对象的translations
    translations = data[0].get("translations")
    if not translations or not isinstance(translations, list) or len(translations) == 0:
        raise Exception("翻译 API 未返回翻译文本。")

    translated_text = translations[0].get("text")
    if not translated_text:
        raise Exception("翻译 API 未返回翻译文本。")

    return translated_text


