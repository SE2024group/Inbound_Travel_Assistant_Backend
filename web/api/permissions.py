# web/api/permissions.py

from rest_framework import permissions

class IsOwnerOrAdmin(permissions.BasePermission):
    """
    自定义权限，允许评论的所有者或管理员用户删除评论。
    """

    def has_object_permission(self, request, view, obj):
        # 安全的方法（如GET）允许所有人访问
        if request.method in permissions.SAFE_METHODS:
            return True

        # 只有管理员或评论的所有者可以执行非安全方法
        return request.user and (request.user.is_staff or obj.user == request.user)
