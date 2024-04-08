# Create your views here.
from django.contrib.auth.hashers import make_password
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import User
from rest_framework import status,serializers
from drf_spectacular.utils import extend_schema, OpenApiResponse, inline_serializer
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate


# 登录
class LoginView(APIView):
    @extend_schema( # 接口装饰器
        tags=['登录、注册'],
        summary='用户登录',
        description='用户通过用户名和密码登录，成功返回JWT。',
        request=inline_serializer(
            name='LoginRequest',
            fields={
                'username': serializers.CharField(),
                'password': serializers.CharField()
            }
        ),
        responses={
            200: inline_serializer(
                name='LoginSuccessResponse',
                fields={
                    'message': serializers.CharField(),
                    'token': serializers.CharField(),
                    'id': serializers.IntegerField(),
                    'username': serializers.CharField(),
                    'role': serializers.ChoiceField(choices=['学生', '教师'])  # 假设这是所有可能的角色
                }
            ),
            400: OpenApiResponse(description='密码错误'),
            404: OpenApiResponse(description='用户不存在')
        },
    )
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        user = authenticate(username=username, password=password)  # 使用Django的authenticate方法
        if user is not None:
            refresh = RefreshToken.for_user(user)
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'id':user.pk,
                'username': user.username,
                'role': user.role  # 确保你的用户模型有role字段
            }, status=status.HTTP_200_OK)
        else:
            return Response({'error': '用户名或密码错误'}, status=status.HTTP_401_UNAUTHORIZED)


# 注册
class RegisterView(APIView):
    @extend_schema(
        tags=['登录、注册'],
        summary='用户注册',
        description='用户提供用户名、密码和角色来注册新账号。',
        request=inline_serializer(
            name='RegisterRequest',
            fields={
                'username': serializers.CharField(),
                'password': serializers.CharField(),
                'role': serializers.ChoiceField(choices=['教师', '学生'], default='学生')
            }
        ),
        responses={
            201: inline_serializer(
                name='RegisterSuccessResponse',
                fields={
                    'message': serializers.CharField(),
                    'id': serializers.IntegerField(),
                }
            ),
            400: OpenApiResponse(description='缺少必要信息或信息格式错误'),
            409: OpenApiResponse(description='用户已存在')
        },
    )
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')
        role = request.data.get('role') 

        if not username or not password or not role:
            return Response({'error': '请填写完整的信息'}, status=status.HTTP_400_BAD_REQUEST)
        
        if User.objects.filter(username=username).exists():
            return Response({'error': '用户已存在'}, status=status.HTTP_409_CONFLICT)
        
        user = User.objects.create(
            username=username,
            password=make_password(password),
            role=role
        )
        return Response({'message': '账号创建成功', 'id': user.pk}, status=status.HTTP_201_CREATED)