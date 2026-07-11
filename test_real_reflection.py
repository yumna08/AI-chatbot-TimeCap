import django
import os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timecapsule.settings')
django.setup()

from django.contrib.auth.models import User
from capsules.models import Capsule
from django.utils import timezone
import datetime

user = User.objects.get(username="testuser")

Capsule.objects.create(
    user=user,
    title="Burnout",
    content="I feel burnt out and struggling to keep up with the daily grind. I think I bit off more than I can chew this semester.",
    mood="stressed",
    unlock_date=timezone.now() - datetime.timedelta(days=90)
)
Capsule.objects.create(
    user=user,
    title="Milestone win",
    content="Energized after finishing the first major milestone on my project. Turns out taking it one step at a time actually works.",
    mood="motivated",
    unlock_date=timezone.now() - datetime.timedelta(days=25)
)

from capsules.ai.reflect import generate_reflection
result = generate_reflection(user, "how have I been feeling about my goals lately")
print(result["reflection"])
print(result["referenced_capsules"])
