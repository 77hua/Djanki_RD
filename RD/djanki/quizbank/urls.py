from django.urls import path
from .views import CourseView,CourseDetailView,CourseCategoryView,CourseCategoryDetailView,QuestionCreateView,CourseSupportObjectivesView,UpdateCategoryTreeView

urlpatterns = [
    path('courses/', CourseView.as_view(), name='course-list-create'),# 获取、添加课程学习
    path('courses/<int:pk>/', CourseDetailView.as_view(), name='course-delete'),  # 删除、修改课程信息
    path('courses/<int:course_id>/category/', CourseCategoryView.as_view(), name='add-category'), # 获取、添加知识点
    path('courses/<int:course_id>/category/<int:category_id>/', CourseCategoryDetailView.as_view(), name='course-category-detail'),# 删除、修改知识点
    path('courses/<int:course_id>/tree-update/', UpdateCategoryTreeView.as_view(), name='tree-update'),# 更新树结构
    path('courses/<int:course_id>/questions/', QuestionCreateView.as_view(), name='create-category'), # 试题创建、获取
    path('question/<int:course_id>/support-objectives/',CourseSupportObjectivesView.as_view(),name='course-support-objectives') # 课程支撑
]
