from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from capsules.ai.ingest import reindex_user

class Command(BaseCommand):
    help = 'Reindexes all capsules for all users in Chroma DB'

    def handle(self, *args, **options):
        users = User.objects.all()
        for user in users:
            self.stdout.write(f"Reindexing user {user.username} (ID: {user.id})...")
            reindex_user(user)
            self.stdout.write(self.style.SUCCESS(f"Successfully reindexed user {user.username}."))
            
        self.stdout.write(self.style.SUCCESS("All users reindexed successfully."))
