from django.urls import path
from .views import CourseQuestionStatsView,StartLearningView,StartReviewView

urlpatterns = [
  path('courses/<int:course_id>/question-stats/', CourseQuestionStatsView.as_view(), name='course-question-stats'), # 学习情况
  path('courses/<int:course_id>/question-learn/', StartLearningView.as_view(), name='course-question-stats'), # 学习试题
  path('courses/<int:course_id>/question-review/', StartReviewView.as_view(), name='course-question-stats'), # 复习试题
]