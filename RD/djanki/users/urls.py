from django.urls import path
from .views import CourseQuestionStatsView,StartLearningView,StartReviewView,BulkUpdateOrCreateLearningRecordsView,LearningStatisticsView

urlpatterns = [
  path('courses/<int:course_id>/question-stats/', CourseQuestionStatsView.as_view(), name='course-question-stats'), # 学习情况
  path('courses/<int:course_id>/question-learn/', StartLearningView.as_view(), name='course-question-stats'), # 学习试题
  path('courses/<int:course_id>/question-review/', StartReviewView.as_view(), name='course-question-stats'), # 复习试题
  path('courses/learning-records/', BulkUpdateOrCreateLearningRecordsView.as_view(), name='bulk-update-create-learning-records'), # 更新学习记录
  path('courses/learning-statistics/', LearningStatisticsView.as_view(), name='bulk-update-create-learning-records'), # 学习统计
]