from django.core.management.base import BaseCommand
from django.utils import timezone
from capsules.models import Capsule, Notification

class Command(BaseCommand):
    help = 'Checks for newly unlocked capsules and creates notifications'

    def handle(self, *args, **options):
        now = timezone.now()
        
        # Find capsules that are unlocked and do not have a notification yet
        # Using filter logic:
        # unlock_date <= now
        # not exists in Notification for this capsule
        newly_unlocked = Capsule.objects.filter(
            unlock_date__lte=now,
            notifications__isnull=True
        )
        
        count = 0
        for capsule in newly_unlocked:
            Notification.objects.create(
                user=capsule.user,
                capsule=capsule,
                message=f"Your capsule '{capsule.title}' from {capsule.created_at.date()} is now unlocked!"
            )
            count += 1
            
        self.stdout.write(self.style.SUCCESS(f'Created {count} notifications for newly unlocked capsules.'))
