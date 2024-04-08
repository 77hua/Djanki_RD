from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status,serializers
from .serializers import CourseSerializer
from .models import Course  # 确保从你的模型中正确导入Course模型
from drf_spectacular.utils import extend_schema,inline_serializer,OpenApiResponse

# 课程列表
class CourseListView(APIView):
    permission_classes = [IsAuthenticated]  # 可选，根据你的权限需求决定是否需要
    @extend_schema(
        tags=['课程管理'],
        summary='获取所有课程',
        description='返回数据库中所有课程的列表。',
        responses={200: CourseSerializer(many=True)}
    )
    def get(self, request):
        courses = Course.objects.all()
        serializer = CourseSerializer(courses, many=True)
        return Response(serializer.data)

# 课程创建
class CourseCreateView(APIView):
    permission_classes = [IsAuthenticated]
    @extend_schema(
        tags=['课程管理'],
        summary='创建课程',
        description='用户可以通过提供课程名和课程简介来创建新的课程。如果课程名和课程简介相同，则会返回错误。',
        request=CourseSerializer,  # 如果你的CourseSerializer已经定义了请求的结构，可以直接使用
        responses={
            201: inline_serializer(
                name='CourseCreateSuccessResponse',
                fields={
                    'message': serializers.CharField(),
                    'course': CourseSerializer(),  # 假设你希望返回创建的课程的详细信息
                }
            ),
            400: OpenApiResponse(description='已存在具有相同课程名和课程简介的课程或其他验证错误'),
        },
    )
    def post(self, request):
        serializer = CourseSerializer(data=request.data)
        if serializer.is_valid():
            name = serializer.validated_data['name']
            description = serializer.validated_data['description']
            
            # 检查数据库中是否已存在具有相同名称和简介的课程
            if Course.objects.filter(name=name, description=description).exists():
                return Response(
                    {"error": "已存在具有相同课程名和课程简介的课程"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # 不存在相同名称和简介的课程，保存新课程
            serializer.save()
            return Response(
                {"message": "课程创建成功", "course": serializer.data},
                status=status.HTTP_201_CREATED
            )
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
# 课程删除
class CourseDeleteView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['课程管理'],
        summary='删除课程',
        description='通过课程ID删除指定的课程。',
        responses={
            204: OpenApiResponse(description='课程删除成功'),
            404: OpenApiResponse(description='课程未找到'),
            403: OpenApiResponse(description='无权限执行此操作')
        }
    )
    def delete(self, request, pk):
        try:
            course = Course.objects.get(pk=pk)
            course.delete()
            return Response({'message': '课程删除成功'},status=status.HTTP_204_NO_CONTENT)
        except Course.DoesNotExist:
            return Response({'error': '课程未找到'}, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            # 可以根据需要处理其他异常
            return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)

