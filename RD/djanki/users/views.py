from rest_framework.views import APIView
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework import serializers,status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from quizbank.models import Course, Question  # 引入quizbank应用的模型
from .models import LearningRecord
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

        # 获取课程下所有试题数量
        total_questions_count = Question.objects.filter(course=course).count()

        # 获取用户在此课程中的学习记录，包括reviewing和mastered状态
        learning_records = LearningRecord.objects.filter(user=request.user, question__course=course)
        reviewing_count = learning_records.filter(status='reviewing').count()
        mastered_count = learning_records.filter(status='mastered').count()

        # 未学习的试题数量
        not_learned_count = total_questions_count - (reviewing_count + mastered_count)

        return Response({
            'course_id': course_id,
            'course_name': course.name,
            'learning_status': {
                'not_learned': not_learned_count,
                'reviewing': reviewing_count,
                'mastered': mastered_count
            }
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
            return Response({"message": "暂无要学习试题！"}, status=200)


# 获取已学习的试题 
class StartReviewView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, course_id):
        today = timezone.now().date()
        question_num = int(request.query_params.get('question_num', 5))  # 从查询参数中获取 question_num
        course = get_object_or_404(Course, id=course_id)

        # 查询用户在指定课程中已学习且计划复习日期小于或等于今天的试题
        review_records = LearningRecord.objects.filter(
            user=request.user,
            question__course=course,
            next_review_date__lte=today  # 只选择需要复习的（即复习日期小于或等于今天的）
        ).select_related('question').order_by('next_review_date')[:question_num]

        # 获取这些记录对应的试题
        questions_to_review = [record.question for record in review_records]

        if questions_to_review:
            return Response(QuestionSerializer(questions_to_review, many=True).data)
        else:
            return Response({"message": "今天暂时无需要复习的试题！"}, status=200)

# 更新学习记录
class BulkUpdateOrCreateLearningRecordsView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        updates = request.data.get('updates', [])
        response_data = []
        errors = []
        for update in updates:
            question_id = update.get('question_id')
            quality_score = update.get('quality_score')
            try:
                question = Question.objects.get(pk=question_id)
                quality_score = int(quality_score)
                course = question.course  # 确保从问题中获取课程信息
                if not (0 <= quality_score <= 5):
                    raise ValueError("质量评分必须在0到5之间")

                learning_record, created = LearningRecord.objects.get_or_create(
                    user=request.user,
                    question=question,
                    course=course,
                    defaults={
                        'next_review_date': timezone.now().date(),
                        'last_review_date': timezone.now().date(),
                        'ef': 2.5,
                        'interval': 1,
                        'status': 'learning'
                    }
                )
                # 更新学习参数
                learning_record.update_learning_parameters(quality_score)
                
                response_data.append({
                    'question_id': question_id,
                    'message': 'Updated successfully',
                    'created': created
                })
            except Exception as e:
                errors.append({
                    'question_id': question_id,
                    'error': str(e)
                })

        if errors:
            return Response({'errors': errors}, status=400)
        return Response(response_data, status=200)