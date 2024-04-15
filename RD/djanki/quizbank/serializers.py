from rest_framework import serializers
from .models import Course,Category,Question,QuestionType,SupportObjective

# 课程序列化
class CourseSerializer(serializers.ModelSerializer):
    class Meta:
        model = Course
        fields = ['id','name', 'description']

# 知识点序列化
class RecursiveSerializer(serializers.Serializer):
    def to_representation(self, value):
        serializer = self.parent.parent.__class__(value, context=self.context)
        return serializer.data

class CategorySerializer(serializers.ModelSerializer):
    children = RecursiveSerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = ('id', 'name', 'parent', 'is_knowledge_point', 'order', 'children')

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # 为顶层知识点设置parent_id为None
        representation['parent_id'] = instance.parent_id if instance.parent else None
        return representation

# 试题创建序列化
class QuestionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Question
        fields = [
            'id', 'question_type', 'summary', 'content_markdown',
            'answer_markdown', 'answer_json', 'explanation_markdown',
            'categories', 'support_objectives'
        ]

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        representation['question_type'] = instance.question_type.description
        representation['categories'] = [{'id': cat.id, 'name': cat.name} for cat in instance.categories.all()]
        representation['support_objectives'] = [{'id': obj.id, 'name': obj.name} for obj in instance.support_objectives.all()]
        return representation

    question_type = serializers.PrimaryKeyRelatedField(queryset=QuestionType.objects.all())
    categories = serializers.PrimaryKeyRelatedField(queryset=Category.objects.filter(is_knowledge_point=True), many=True)
    support_objectives = serializers.PrimaryKeyRelatedField(queryset=SupportObjective.objects.all(), many=True)

# 课程支撑
class SupportObjectiveSerializer(serializers.ModelSerializer):
    class Meta:
        model = SupportObjective
        fields = ['id', 'name', 'description', 'order']
        extra_kwargs = {'order': {'required': False}}