# web/api/utils.py

import requests
from django.conf import settings

def translate_text(text, from_lang, to_lang):
    """
    调用翻译 API 将文本从 from_lang 翻译到 to_lang。
    
    :param text: 要翻译的文本
    :param from_lang: 原文语言类型（如 "ZH"、"EN"）
    :param to_lang: 目标语言类型（如 "EN"、"ZH"）
    :return: 翻译后的文本
    :raises: Exception 如果翻译失败
    """
    url = settings.TRANSLATE_API_URL
    payload = {
        "ColaKey": settings.COLA_KEY,
        "text": text,
        "fromlang": from_lang,
        "tolang": to_lang,
    }
    headers = {
        "Content-Type": "application/json",
    }
    
    response = requests.post(url, json=payload, headers=headers)
    
    if response.status_code != 200:
        raise Exception(f"翻译 API 请求失败，状态码：{response.status_code}")
    
    data = response.json()
    
    # 根据实际 API 响应格式调整
    # 假设成功响应包含 'translated_text' 字段
    if data.get("code") != 0:
        raise Exception(f"翻译 API 错误：{data.get('msg')}")
    
    translated_text = data.get("data", {}).get("dst")
    
    if not translated_text:
        raise Exception("翻译 API 未返回翻译文本。")
    
    return translated_text
