from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from rest_framework import serializers
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from quizbank.models import Course, Question  # 引入quizbank应用的模型
from .models import LearningRecord,CourseLearningStatus
from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer

# 获取某用户的某课程学习情况
class CourseQuestionStatsView(APIView):
    permission_classes = [IsAuthenticated]
    @extend_schema(
        tags=['课程学习情况'],
        summary="获取用户的课程学习情况",
        description="返回指定课程中用户的学习状态，包括未学习、复习中和已掌握的试题数量。",
        responses={
            200: inline_serializer(
                name='CourseLearningStatusResponse',
                fields={
                    'course_id': serializers.IntegerField(),
                    'course_name': serializers.CharField(),
                    'learning_status': inline_serializer(
                        name='LearningStatusDetails',
                        fields={
                            'not_learned': serializers.IntegerField(),
                            'reviewing': serializers.IntegerField(),
                            'mastered': serializers.IntegerField()
                        }
                    )
                }
            ),
            404: OpenApiResponse(description="课程未找到")
        },
    )
    def get(self, request, course_id):
        # 确保课程存在
        course = get_object_or_404(Course, pk=course_id)
        # 尝试获取用户在此课程中的学习状态
        try:
            learning_status = CourseLearningStatus.objects.get(course=course, user=request.user)
            stats = {
                'not_learned': learning_status.learning,
                'reviewing': learning_status.reviewing,
                'mastered': learning_status.mastered
            }
            
        except CourseLearningStatus.DoesNotExist:
            # 如果还没有记录，表示用户还没有开始学习这个课程的任何内容
            stats = {
                'not_learned': Question.objects.filter(course=course).count(),
                'reviewing': 0,
                'mastered': 0
            }

        return Response({
            'course_id': course_id,
            'course_name': course.name,
            'learning_status': stats
        })