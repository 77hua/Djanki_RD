from django.urls import path
from .views import CourseQuestionStatsView

urlpatterns = [
  path('courses/<int:course_id>/question-stats/', CourseQuestionStatsView.as_view(), name='course-question-stats'), # 学习情况
]