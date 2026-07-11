import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timecapsule.settings')
django.setup()

from django.contrib.auth.models import User
from capsules.models import Capsule

def list_users():
    users = User.objects.all().order_by('id')
    print(f"{'ID':<5} | {'Username':<30} | {'Is Superuser':<12} | {'Capsule Count'}")
    print("-" * 70)
    for u in users:
        capsule_count = Capsule.objects.filter(user=u).count()
        print(f"{u.id:<5} | {u.username:<30} | {str(u.is_superuser):<12} | {capsule_count}")

if __name__ == '__main__':
    list_users()
