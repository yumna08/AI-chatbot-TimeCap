from rest_framework import serializers
from .models import Capsule, ReflectionQuery

class CapsuleSerializer(serializers.ModelSerializer):
    is_unlocked = serializers.ReadOnlyField()

    class Meta:
        model = Capsule
        fields = ['id', 'user', 'title', 'content', 'mood', 'created_at', 'unlock_date', 'tags', 'is_unlocked']
        read_only_fields = ['user', 'created_at']

class ReflectionQuerySerializer(serializers.ModelSerializer):
    class Meta:
        model = ReflectionQuery
        fields = ['id', 'user', 'question', 'response', 'created_at']
        read_only_fields = ['user', 'created_at']

from .models import Notification

class NotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ['id', 'capsule', 'message', 'created_at', 'is_read']
        read_only_fields = ['capsule', 'message', 'created_at']
