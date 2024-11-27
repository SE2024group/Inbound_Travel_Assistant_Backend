from django.urls import path
from .views import EchoView, LoginView, UserInfoView, OCRView, DishDetailView

urlpatterns = [
    path('echo/', EchoView.as_view(), name='echo'),
    path('login/', LoginView.as_view(), name='login'),
    path('userinfo/', UserInfoView.as_view(), name='userinfo'),
    path('ocr/', OCRView.as_view(), name='ocr'),
    path('dish/<int:id>/', DishDetailView.as_view(), name='dish-detail'),

]
