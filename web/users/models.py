# web/users/models.py

from django.contrib.auth.models import AbstractUser
from django.db import models
from django.utils import timezone
import os
import uuid


def user_avatar_upload_to(instance, filename):
    # 获取文件扩展名
    ext = os.path.splitext(filename)[1]
    # 使用uuid生成唯一文件名
    new_filename = f"{uuid.uuid4().hex}{ext}"
    return os.path.join('avatars', str(instance.id), new_filename)

class CustomUser(AbstractUser):
    nickname = models.CharField(max_length=150, blank=True)
    avatar = models.ImageField(upload_to=user_avatar_upload_to, blank=True, null=True)
    personality_description = models.TextField(blank=True, null=True)
    signup_date = models.DateField(null=True, blank=True, help_text="用户注册日期（年月日）")
    
    # 新增字段
    religious_belief = models.CharField(
        max_length=100, 
        blank=True, 
        null=True, 
        help_text="用户的宗教信仰"
    )
    dietary_restrictions = models.JSONField(
        blank=True, 
        null=True, 
        help_text="用户的饮食禁忌列表（字符串列表）",
        default=list  # 默认值为空列表
    )

    def __str__(self):
        return self.username
