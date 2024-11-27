# api/models.py

from django.db import models

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
