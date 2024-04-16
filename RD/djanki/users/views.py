from rest_framework.views import APIView
from django.shortcuts import get_object_or_404
from rest_framework import serializers,status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from quizbank.models import Course, Question  # 引入quizbank应用的模型
from .models import LearningRecord,CourseLearningStatus
from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer
from .serializers import LearningRecordSerializer
from quizbank.serializers import QuestionSerializer

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

# 获取未学习的试题
class StartLearningView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['课程学习情况'],
    )
    def get(self, request, course_id):
        question_num = int(request.query_params.get('question_num', 5))  # 默认返回5题，如果没有指定则返回5题
        course = get_object_or_404(Course, id=course_id)

        learned_questions = LearningRecord.objects.filter(
            user=request.user,
            question__course=course
        ).values_list('question_id', flat=True)

        # 获取尚未学习的试题，并限制返回的数量
        new_questions = Question.objects.filter(course=course).exclude(id__in=learned_questions)[:question_num]

        if new_questions.exists():
            return Response(QuestionSerializer(new_questions, many=True).data)
        else:
            return Response({"message": "暂无要学习试题！"}, status=404)


# 获取已学习的试题 
class StartReviewView(APIView):
    permission_classes = [IsAuthenticated]
    
    @extend_schema(
        tags=['课程学习情况'],
    )
    def get(self, request, course_id):
        question_num = int(request.query_params.get('question_num', 5))  # 默认返回5题，如果没有指定则返回5题
        course = get_object_or_404(Course, id=course_id)

        review_questions = LearningRecord.objects.filter(
            user=request.user,
            question__course=course
        ).values_list('question_id', flat=True)

        # 获取需要复习的试题，并限制返回的数量
        questions_to_review = Question.objects.filter(id__in=review_questions)[:question_num]

        if questions_to_review.exists():
            return Response(QuestionSerializer(questions_to_review, many=True).data)
        else:
            return Response({"message": "今天暂时没有要复习的试题！"}, status=404)

# 更新已学习试题的记录（算法核心）
class UpdateLearningRecordView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, record_id):
        # 获取学习记录
        learning_record = get_object_or_404(LearningRecord, pk=record_id, user=request.user)

        # 获取评分
        quality_score = request.data.get('quality_score')
        if quality_score is None:
            return Response({"error": "质量评分是必须的。"}, status=status.HTTP_400_BAD_REQUEST)

        try:
            quality_score = int(quality_score)
        except ValueError:
            return Response({"error": "质量评分必须是整数。"}, status=status.HTTP_400_BAD_REQUEST)

        # 更新学习参数
        try:
            learning_record.update_learning_parameters(quality_score)
            return Response({"message": "学习记录已更新。"}, status=status.HTTP_200_OK)
        except ValueError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)