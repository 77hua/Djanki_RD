from rest_framework import serializers
from .models import LearningRecord

class LearningRecordSerializer(serializers.ModelSerializer):
   class LearningRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningRecord
        fields = '__all__'  # 或者指定需要序列化的字段
        read_only_fields = ('user', 'question', 'next_review_date', 'repetition', 'ef', 'last_review_date')  # 防止这些字段被外部修改