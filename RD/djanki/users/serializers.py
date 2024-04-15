from rest_framework import serializers
from .models import LearningRecord

class LearningRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = LearningRecord
        fields = '__all__'