from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone

class CapsuleManager(models.Manager):
    def unlocked_for(self, user):
        return self.filter(user=user, unlock_date__lte=timezone.now()).order_by('-unlock_date')

class Capsule(models.Model):
    MOOD_CHOICES = [
        ('happy', 'Happy'),
        ('excited', 'Excited'),
        ('stressed', 'Stressed'),
        ('sad', 'Sad'),
        ('motivated', 'Motivated'),
        ('neutral', 'Neutral'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='capsules')
    title = models.CharField(max_length=255)
    content = models.TextField()
    mood = models.CharField(max_length=20, choices=MOOD_CHOICES)
    created_at = models.DateTimeField(auto_now_add=True)
    unlock_date = models.DateTimeField()
    tags = models.JSONField(default=list, blank=True)
    
    objects = CapsuleManager()

    @property
    def is_unlocked(self):
        return timezone.now() >= self.unlock_date

    def __str__(self):
        return f"{self.title} by {self.user.username}"


class ReflectionQuery(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='reflections')
    question = models.TextField()
    response = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Reflection by {self.user.username} at {self.created_at}"

class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    capsule = models.ForeignKey(Capsule, on_delete=models.CASCADE, related_name='notifications')
    message = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification for {self.user.username} - Read: {self.is_read}"
