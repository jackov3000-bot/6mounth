from rest_framework import serializers
from .models import Course

class CourseSerializer(serializers.ModelSerializer):
    owner = serializers.CharField(source='owner.username', read_only=True)

    class Meta:
        model = Course
        fields = ['id', 'title', 'owner', 'created_at']