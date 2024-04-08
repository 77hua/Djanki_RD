from django.urls import path
from .views import CourseCreateView,CourseListView,CourseDeleteView

urlpatterns = [
    path('courses/', CourseListView.as_view(), name='course-list'), # 获取课程list
    path('course-create/', CourseCreateView.as_view(), name='course-create'), # 创建课程
    path('courses-delete/<int:pk>/', CourseDeleteView.as_view(), name='course-delete'), # 删除课程
]
