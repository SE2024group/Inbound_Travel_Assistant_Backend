# web/users/admin.py

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser

class CustomUserAdmin(UserAdmin):
    model = CustomUser
    # 添加自定义字段到用户管理界面
    fieldsets = UserAdmin.fieldsets + (
        (None, {'fields': ('nickname', 'avatar', 'personality_description')}),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        (None, {'fields': ('nickname', 'avatar', 'personality_description')}),
    )

admin.site.register(CustomUser, CustomUserAdmin)
