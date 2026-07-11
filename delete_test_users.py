import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timecapsule.settings')
django.setup()

from django.contrib.auth.models import User

def delete_users():
    usernames = ['testuser', 'searchtest', 'reflecttest', 'apitest']
    for username in usernames:
        try:
            user = User.objects.get(username=username)
            user.delete()
            print(f"Deleted user: {username}")
        except User.DoesNotExist:
            print(f"User not found: {username}")

if __name__ == '__main__':
    delete_users()
