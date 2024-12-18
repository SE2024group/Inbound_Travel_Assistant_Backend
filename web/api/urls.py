from django.urls import path
from .views import (
    EchoView, RegisterView, LoginView, UserDetailView,
    BrowsingHistoryListView, LikeHistoryListView,
    FavoriteHistoryListView, CommentHistoryListView,
    OCRView, DishDetailView, LogoutView, VoiceTranslationView,
    UpdateUserPreferencesView, TextTranslationView, DishSearchView,
    TagListView, AdvancedSearchView, FavoriteToggleView, FavoriteListView
)

urlpatterns = [
    path('echo/', EchoView.as_view(), name='echo'),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('user/', UserDetailView.as_view(), name='user-detail'),
    path('user/preferences/', UpdateUserPreferencesView.as_view(), name='user-preferences'),
    path('browsing-history/', BrowsingHistoryListView.as_view(), name='browsing-history'),
    path('like-history/', LikeHistoryListView.as_view(), name='like-history'),
    path('favorite-history/', FavoriteHistoryListView.as_view(), name='favorite-history'),
    path('comment-history/', CommentHistoryListView.as_view(), name='comment-history'),
    path('ocr/', OCRView.as_view(), name='ocr'),
    path('dish/<int:pk>/', DishDetailView.as_view(), name='dish-detail'),
    path('voice-translation/', VoiceTranslationView.as_view(), name='voice-translation'),
    path('text-translation/', TextTranslationView.as_view(), name='text-translation'),  # 新增文字翻译端点
    path('dish/search/', DishSearchView.as_view(), name='dish-search'),  # 新的搜索接口
    path('dish/advanced_search/', AdvancedSearchView.as_view(), name='advanced-dish-search'),  # 添加进阶搜索路由
    path('tags/', TagListView.as_view(), name='tag-list'),  # 添加标签列表路由
    path('favorite/<int:dish_id>/', FavoriteToggleView.as_view(), name='favorite-toggle'),  # 收藏与取消收藏
    path('favorites/', FavoriteListView.as_view(), name='favorite-list'),  # 获取收藏列表

]
