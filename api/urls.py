from django.urls import path
from .views import EchoView, LoginView, UserInfoView, OCRView

urlpatterns = [
    path('echo/', EchoView.as_view(), name='echo'),
    path('login/', LoginView.as_view(), name='login'),
    path('userinfo/', UserInfoView.as_view(), name='userinfo'),
    path('ocr/', OCRView.as_view(), name='ocr'),

]
