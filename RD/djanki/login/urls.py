from django.urls import path
from .views import LoginView,RegisterView


urlpatterns = [
    path('login/', LoginView.as_view(), name='login'), # 登录
    path('register/', RegisterView.as_view(), name='register'), # 注册
]