from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework import status,serializers
from .serializers import CourseSerializer,CategorySerializer,QuestionSerializer,SupportObjectiveSerializer
from .models import Course,Category,Question,SupportObjective,QuestionImage
from drf_spectacular.utils import extend_schema,inline_serializer,OpenApiResponse
from django.db.models import F,Max
from django.db import transaction
from django.shortcuts import get_object_or_404
from django.core.files.storage import FileSystemStorage
from django.http import JsonResponse
from .func import remove_markdown_images

# 课程列表、添加
class CourseView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        methods=['GET'],
        tags=['课程管理'],
        summary='获取所有课程',
        description='返回数据库中所有课程的列表。',
        responses={200: CourseSerializer(many=True)}
    )
    def get(self, request):
        courses = Course.objects.all()
        serializer = CourseSerializer(courses, many=True)
        return Response(serializer.data)

    @extend_schema(
        methods=['POST'],
        tags=['课程管理'],
        summary='创建课程',
        description='用户可以通过提供课程名和课程简介来创建新的课程。如果课程名和课程简介相同，则会返回错误。',
        request=CourseSerializer,
        responses={
            201: inline_serializer(
                name='CourseCreateSuccessResponse',
                fields={
                    'message': serializers.CharField(),
                    'course': CourseSerializer(),
                }
            ),
            400: OpenApiResponse(description='验证错误'),
        },
    )
    def post(self, request):
        serializer = CourseSerializer(data=request.data)
        if serializer.is_valid():
            name = serializer.validated_data['name']
            description = serializer.validated_data['description']
            if Course.objects.filter(name=name, description=description).exists():
                return Response({"error": "已存在具有相同课程名和课程简介的课程"}, status=status.HTTP_400_BAD_REQUEST)
            serializer.save()
            return Response({"message": "课程创建成功", "course": serializer.data}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
# 删除、修改课程
class CourseDetailView(APIView):
    permission_classes = [IsAuthenticated]
    @extend_schema(
        methods=['DELETE'],
        tags=['课程管理'],
        summary='删除课程',
        description='通过课程ID删除指定的课程。',
        responses={
            204: OpenApiResponse(description='课程删除成功'),
            404: OpenApiResponse(description='课程未找到'),
        }
    )
    def delete(self, request, pk=None):
        if not pk:
            return Response({'error': '缺少课程ID'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            course = Course.objects.get(pk=pk)
            course.delete()
            return Response({'message': '课程删除成功'}, status=status.HTTP_204_NO_CONTENT)
        except Course.DoesNotExist:
            return Response({'error': '课程未找到'}, status=status.HTTP_404_NOT_FOUND)
    @extend_schema(
        methods=['PATCH'],
        tags=['课程管理'],
        summary='修改课程',
        description='通过课程ID部分更新指定的课程信息。',
        request=CourseSerializer,
        responses={
            200: CourseSerializer(),
            404: OpenApiResponse(description='课程未找到'),
        },
    )
    def patch(self, request, pk=None):
        try:
            course = Course.objects.get(pk=pk)
            serializer = CourseSerializer(course, data=request.data, partial=True)
            if serializer.is_valid():
                serializer.save()
                return Response(serializer.data, status=status.HTTP_200_OK)
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        except Course.DoesNotExist:
            return Response({'error': '课程未找到'}, status=status.HTTP_404_NOT_FOUND)

# 知识点
class CourseCategoryView(APIView):
    permission_classes = [IsAuthenticated]

    # 根据课程id获取知识点
    @extend_schema(
        tags=['知识点'],
        summary="获取课程的所有知识点",
        responses={200: CategorySerializer(many=True)},
        description="返回指定课程下所有知识点的列表。"
    )
    def get(self, request, course_id):
        # 确保课程存在
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return Response({'error': '课程未找到'}, status=status.HTTP_404_NOT_FOUND)

        # 获取该课程下所有顶层知识点或分类（没有父知识点的知识点）
        categories = Category.objects.filter(course=course, parent__isnull=True)
        serializer = CategorySerializer(categories, many=True)
        return Response(serializer.data)

    # 添加知识点
    @extend_schema(
        tags=['知识点'],
        summary="添加新的知识点到课程",
        request=CategorySerializer,
        responses={201: CategorySerializer},
        description="在指定课程下添加新的知识点。"
    )
    def post(self, request, course_id):
        try:
            course = Course.objects.get(id=course_id)
        except Course.DoesNotExist:
            return Response({'error': '课程未找到'}, status=status.HTTP_404_NOT_FOUND)
        
        # 在这里，我们确保即使`parent`字段没有被提供，也不会导致错误。
        request_data = request.data.copy()
        if 'parent_id' not in request_data or not request_data['parent_id']:
            request_data['parent'] = None
        else:
            # 如果提供了`parent_id`，尝试将其转换为`parent`对象
            try:
                parent_category = Category.objects.get(id=request_data['parent_id'], course=course)
                request_data['parent'] = parent_category.id
            except Category.DoesNotExist:
                return Response({'error': '父知识点未找到'}, status=status.HTTP_404_NOT_FOUND)

        serializer = CategorySerializer(data=request_data)
        if serializer.is_valid():
            serializer.save(course=course)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
class CourseCategoryDetailView(APIView):
    permission_classes = [IsAuthenticated]
    # 删除知识点
    @extend_schema(
        tags=['知识点'],
        summary="删除指定的知识点",
        responses={204: None},
        description="从课程中删除指定ID的知识点。"
    )
    def delete(self, request, course_id, category_id):
        try:
            category = Category.objects.get(course_id=course_id, id=category_id)
        except Category.DoesNotExist:
            return Response({'error': '知识点未找到'}, status=status.HTTP_404_NOT_FOUND)
        
        parent_id = category.parent_id  # 获取被删除知识点的父知识点ID
        category_order = category.order  # 获取被删除知识点的顺序
        category.delete()  # 删除知识点

        # 重新排序：对同一父级下，顺序在被删除知识点之后的所有知识点，其order值递减1
        if category.parent_id is None:
        # 对同一课程下的顶层知识点重新排序
            Category.objects.filter(course_id=course_id, parent__isnull=True, order__gt=category_order).update(order=F('order') - 1)
        else:
            # 对同一父级下，顺序在被删除知识点之后的所有知识点，其order值递减1
            Category.objects.filter(parent_id=category.parent_id, order__gt=category_order).update(order=F('order') - 1)

        return Response(status=status.HTTP_204_NO_CONTENT)
    # 修改知识点
    @extend_schema(
        tags=['知识点'],
        summary="修改指定的知识点",
        request=CategorySerializer,
        responses={200: CategorySerializer},
        description="更新指定ID的知识点的详细信息。",
        methods=['PUT']
    )
    def put(self, request, course_id, category_id):
        try:
            category = Category.objects.get(course_id=course_id, id=category_id)
        except Category.DoesNotExist:
            return Response({'error': '知识点未找到'}, status=status.HTTP_404_NOT_FOUND)
        
        serializer = CategorySerializer(category, data=request.data, partial=True) # 注意这里的 partial=True 参数
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# 拖拽知识点
class UpdateCategoryTreeView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, course_id):
        with transaction.atomic():  # 使用事务确保整个操作的原子性
            # 验证传入的ID对应的实体是否存在
            dragged_node = get_object_or_404(Category, id=request.data.get('draggedId'), course_id=course_id)
            drop_node = get_object_or_404(Category, id=request.data.get('dropId'), course_id=course_id)
            course = get_object_or_404(Course, id=course_id)

            drop_type = request.data.get('type')

            # 确定新的parent和order
            if drop_type == 'inner':
                new_parent = drop_node
                new_order = Category.objects.filter(parent=new_parent,course=course).count() + 1  # 最后的位置
            else:
                new_parent = drop_node.parent
                if drop_type == 'before':
                    new_order = drop_node.order
                elif drop_type == 'after':
                    new_order = drop_node.order + 1

            # 更新被拖拽节点及其子节点的order
            if dragged_node.parent == new_parent:
                # 同一个父节点
                Category.objects.filter(parent=new_parent, course=course, order__gte=new_order).exclude(id=dragged_node.id).update(order=F('order') + 1)
            else:
                # 不同的父节点
                Category.objects.filter(parent=dragged_node.parent, course=course, order__gt=dragged_node.order).update(order=F('order') - 1)
                Category.objects.filter(parent=new_parent, course=course, order__gte=new_order).update(order=F('order') + 1)

            # 更新拖拽节点
            dragged_node.parent = new_parent
            dragged_node.order = new_order
            dragged_node.save()

            # 重新排序所有影响的节点以保证order的连续性
            self.reorder_siblings(new_parent, course)
            if dragged_node.parent != new_parent:
                self.reorder_siblings(dragged_node.parent, course)

        return Response({"message": "Node reordered successfully"})

    def reorder_siblings(self, parent, course):
        siblings = Category.objects.filter(parent=parent, course=course).order_by('order')
        for index, sibling in enumerate(siblings):
            sibling.order = index + 1  # 重新分配order，从1开始
            sibling.save()
        
# 试题创建
class QuestionCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['试题'],
        summary="根据课程ID获取试题",
        responses={200: QuestionSerializer(many=True)},
        description="返回指定课程中所有试题的列表。",
        parameters=[{
            'name': 'course_id',
            'description': '课程的ID'
        }]
    )
    def get(self, request, course_id):
        try:
            course = Course.objects.get(pk=course_id)
        except Course.DoesNotExist:
            return Response({'error': '课程未找到'}, status=status.HTTP_404_NOT_FOUND)
        
        questions = Question.objects.filter(course=course)
        serializer = QuestionSerializer(questions, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=['试题'],
        summary="为指定课程添加新试题",
        request=QuestionSerializer,
        responses={201: QuestionSerializer},
        description="为指定课程创建并返回一个新的试题。",
        parameters=[{
            'name': 'course_id',
            'description': '课程的ID',
            'required': True,
            'type': 'integer',
            'in': 'path'
        }]
    )
    def post(self, request, course_id):
        try:
            course = Course.objects.get(pk=course_id)
        except Course.DoesNotExist:
            return Response({'error': '课程未找到'}, status=status.HTTP_404_NOT_FOUND)

        serializer = QuestionSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            # 将course实例添加到validated_data中
            serializer.save(course=course)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# 上传图片    
class UploadImageView(APIView):

    def post(self, request):
        image_file = request.FILES['image']
        fs = FileSystemStorage()
        filename = fs.save(image_file.name, image_file)
        uploaded_file_url = fs.url(filename)
        return JsonResponse({'message': '图片上传成功', 'url': uploaded_file_url})    
    
# 课程支撑
class CourseSupportObjectivesView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        tags=['支撑目标'],
        summary="获取课程的所有支撑目标",
        responses={200: SupportObjectiveSerializer(many=True)},
        description="根据课程ID返回该课程的所有支撑目标列表。"
    )
    def get(self, request, course_id):
        try:
            course = Course.objects.get(pk=course_id)
        except Course.DoesNotExist:
            return Response({'error': '课程未找到'}, status=status.HTTP_404_NOT_FOUND)

        support_objectives = SupportObjective.objects.filter(course=course).order_by('order')
        serializer = SupportObjectiveSerializer(support_objectives, many=True)
        return Response(serializer.data)

    @extend_schema(
        tags=['支撑目标'],
        summary="为特定课程添加新的支撑目标",
        request=SupportObjectiveSerializer,
        responses={201: SupportObjectiveSerializer},
        description="为指定的课程添加一个新的支撑目标，并返回创建的支撑目标。"
    )
    def post(self, request, course_id):
        try:
            course = Course.objects.get(pk=course_id)
        except Course.DoesNotExist:
            return Response({'error': '课程未找到'}, status=status.HTTP_404_NOT_FOUND)

        data = request.data.copy()
        if 'order' not in data or data['order'] is None:
            last_order = SupportObjective.objects.filter(course=course).aggregate(Max('order'))['order__max']
            data['order'] = (last_order or 0) + 1

        serializer = SupportObjectiveSerializer(data=data)
        if serializer.is_valid():
            support_objective = serializer.save(course=course)
            return Response(SupportObjectiveSerializer(support_objective).data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @extend_schema(
        tags=['支撑目标'],
        summary="删除特定课程的支撑目标",
        responses={
            204: OpenApiResponse(description="支撑目标删除成功"),
            404: OpenApiResponse(description="支撑目标未找到或课程未找到")
        },
        description="根据课程ID和支撑目标ID删除指定的支撑目标。"
    )
    def delete(self, request, course_id, objective_id):
        # 首先确保课程存在
        course = get_object_or_404(Course, pk=course_id)
        # 尝试获取并删除指定的支撑目标
        support_objective = get_object_or_404(SupportObjective, pk=objective_id, course=course)
        support_objective.delete()
        return Response({'message': '支撑目标删除成功'}, status=status.HTTP_204_NO_CONTENT)

    
# 具体试题、修改试题
class QuestionDetailView(APIView):
    permission_classes = [IsAuthenticated]
    def get(self, request, question_id):
        try:
            question = Question.objects.get(pk=question_id)
            serializer = QuestionSerializer(question)
            return Response(serializer.data)
        except Question.DoesNotExist:
            return Response({'error': '没找到该课程'}, status=status.HTTP_404_NOT_FOUND)
    # 修改试题
    def put(self, request, question_id):
        question = get_object_or_404(Question, pk=question_id)

        serializer = QuestionSerializer(question, data=request.data)
        if serializer.is_valid():
            serializer.save()  # 保存修改后的试题
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

# 删除试题
class QuestionDeleteView(APIView):
    permission_classes = [IsAuthenticated]
    def delete(self, request, question_id):
        try:
            question = Question.objects.get(pk=question_id)
            # 删除content_markdown, answer_markdown, explanation_markdown中的图片
            remove_markdown_images(question.content_markdown)
            remove_markdown_images(question.answer_markdown)
            remove_markdown_images(question.explanation_markdown)
            
            # 删除问题本身
            question.delete()
            return Response({'message': '删除成功'}, status=status.HTTP_204_NO_CONTENT)
        except Question.DoesNotExist:
            return Response({'error': '没找到该试题'}, status=status.HTTP_404_NOT_FOUND)
        
# 根据内容搜索试题
class SearchQuestionsView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        search_term = request.query_params.get('query')
        if not search_term:
            return Response(
                {'error': '请提供搜索内容'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # 搜索试题内容、题型等字段
        matching_questions = Question.objects.filter(
            content_markdown__icontains=search_term  # 搜索content_markdown中包含的词语
        )

        # 返回找到的试题
        if matching_questions.exists():
            serializer = QuestionSerializer(matching_questions, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        else:
            return Response(
                {'message': '没有找到相关试题'},
                status=status.HTTP_404_NOT_FOUND
            )       