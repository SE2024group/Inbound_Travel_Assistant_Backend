from django.urls import path
from .views import (
    EchoView, RegisterView, LoginView, UserDetailView,
    BrowsingHistoryListView, LikeHistoryListView,
    FavoriteHistoryListView, CommentHistoryListView,
    OCRView, DishDetailView, LogoutView, VoiceTranslationView
)

urlpatterns = [
    path('echo/', EchoView.as_view(), name='echo'),
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginView.as_view(), name='login'),
    path('logout/', LogoutView.as_view(), name='logout'),
    path('user/', UserDetailView.as_view(), name='user-detail'),
    path('browsing-history/', BrowsingHistoryListView.as_view(), name='browsing-history'),
    path('like-history/', LikeHistoryListView.as_view(), name='like-history'),
    path('favorite-history/', FavoriteHistoryListView.as_view(), name='favorite-history'),
    path('comment-history/', CommentHistoryListView.as_view(), name='comment-history'),
    path('ocr/', OCRView.as_view(), name='ocr'),
    path('dish/<int:pk>/', DishDetailView.as_view(), name='dish-detail'),
    path('voice-translation/', VoiceTranslationView.as_view(), name='voice-translation'),

]
