from rest_framework import serializers
from .models import Course,Category

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