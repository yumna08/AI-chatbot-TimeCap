from rest_framework import serializers
from .models import Capsule, ReflectionQuery


class CapsuleSerializer(serializers.ModelSerializer):
    is_unlocked = serializers.ReadOnlyField()
    photo = serializers.ImageField(required=False, allow_null=True)
    ai_caption = serializers.CharField(read_only=True, allow_null=True)

    def to_representation(self, instance):
        """Ensure locked capsules do not expose sensitive fields.

        This runs for all serializer outputs (list, retrieve, search, reflections)
        and will null-out or remove `content`, `photo`, and `ai_caption` when
        `instance.is_unlocked` is False.
        """
        ret = super().to_representation(instance)
        try:
            unlocked = bool(getattr(instance, 'is_unlocked', True))
        except Exception:
            unlocked = True

        if not unlocked:
            if 'content' in ret:
                ret['content'] = None
            if 'photo' in ret:
                ret['photo'] = None
            if 'ai_caption' in ret:
                ret['ai_caption'] = None

        return ret

    class Meta:
        model = Capsule
        fields = ['id', 'user', 'title', 'content', 'mood', 'created_at', 'unlock_date', 'tags', 'is_unlocked', 'photo', 'ai_caption']
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
