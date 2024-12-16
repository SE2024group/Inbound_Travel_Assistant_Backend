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
    print(os.path.join('avatars', str(instance.id), new_filename),'-----------------')
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
    # 使用 ManyToManyField 通过 DietaryPreference 中间模型关联 Tag
    dietary_restrictions = models.ManyToManyField(
        'api.Tag',  # 使用字符串引用
        through='api.DietaryPreference',  # 使用字符串引用
        related_name='users_with_preferences',
        blank=True,
        help_text="用户的饮食偏好（喜爱、不喜爱、其他）"
    )

    def __str__(self):
        return self.username
