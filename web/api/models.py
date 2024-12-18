# api/models.py
from django.conf import settings
from django.db import models


class BrowsingHistory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='browsing_history')
    dish = models.ForeignKey('Dish', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Browsing History'
        verbose_name_plural = 'Browsing Histories'

    def __str__(self):
        return f"{self.user.username} viewed {self.dish.name} at {self.timestamp}"


class LikeHistory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='like_history')
    dish = models.ForeignKey('Dish', on_delete=models.CASCADE)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Like History'
        verbose_name_plural = 'Like Histories'

    def __str__(self):
        return f"{self.user.username} liked {self.dish.name} at {self.timestamp}"

class FavoriteHistory(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='favorite_history')
    dish = models.ForeignKey('Dish', on_delete=models.CASCADE, related_name='favorite_histories')  # 添加 related_name
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Favorite History'
        verbose_name_plural = 'Favorite Histories'

    def __str__(self):
        return f"{self.user.username} favorited {self.dish.name} at {self.timestamp}"

class CommentHistory(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='comment_history'
    )
    dish = models.ForeignKey('Dish', on_delete=models.CASCADE, related_name='comments')
    comment = models.TextField()
    rating = models.IntegerField(
        choices=[(i, i) for i in range(6)],
        default=0,
        help_text="评分分数（0-5）"
    )
    timestamp = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-timestamp']
        verbose_name = 'Comment History'
        verbose_name_plural = 'Comment Histories'

    def __str__(self):
        return f"{self.user.username} commented on {self.dish.name} at {self.timestamp}"

import os
import uuid
def comment_image_upload_to(instance, filename):
    """
    生成评论图片的唯一文件名，并指定上传路径。
    
    :param instance: CommentImage 实例
    :param filename: 原始文件名
    :return: 唯一化的文件路径
    """
    # 获取文件扩展名
    ext = os.path.splitext(filename)[1]
    # 生成唯一文件名
    new_filename = f"{uuid.uuid4().hex}{ext}"
    # 定义上传路径，按评论ID组织文件夹
    return os.path.join('comment_images', str(instance.comment.id), new_filename)




class CommentImage(models.Model):
    comment = models.ForeignKey(
        CommentHistory,
        related_name='images',
        on_delete=models.CASCADE
    )
    image = models.ImageField(upload_to=comment_image_upload_to)
    
    def __str__(self):
        return f"Image for comment {self.comment.id}"
class Tag(models.Model):
    name = models.CharField(max_length=50)
    name_en = models.CharField(max_length=50, null=True, blank=True)  # 英文标签名
    
    def __str__(self):
        return self.name

class Dish(models.Model):
    name = models.CharField(max_length=100)
    name_en = models.CharField(max_length=100, null=True, blank=True)  # 英文名称
    description = models.TextField()
    description_en = models.TextField(null=True, blank=True)  # 英文描述
    tags = models.ManyToManyField(Tag, related_name='dishes')

    def __str__(self):
        return self.name

class Image(models.Model):
    dish = models.ForeignKey(Dish, related_name='images', on_delete=models.CASCADE)
    image_url = models.URLField(max_length=200)

    def __str__(self):
        return f"Image of {self.dish.name}"


class DietaryPreference(models.Model):
    PREFERENCE_CHOICES = [
        ('LIKE', '喜爱'),
        ('DISLIKE', '不喜爱'),
        ('OTHER', '其他'),
    ]

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='dietary_preferences')
    tag = models.ForeignKey(Tag, on_delete=models.CASCADE, related_name='dietary_preferences')
    preference = models.CharField(max_length=7, choices=PREFERENCE_CHOICES)

    class Meta:
        unique_together = ('user', 'tag')  # 每个用户每个标签只有一条记录

    def __str__(self):
        return f"{self.user.username} - {self.tag.name} - {self.get_preference_display()}"
