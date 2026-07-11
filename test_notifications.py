import os
import django
import subprocess
import requests

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timecapsule.settings')
django.setup()

import datetime
from django.utils import timezone
from django.contrib.auth.models import User
from capsules.models import Capsule
import uuid

def run_test():
    test_username = f"testuser_{uuid.uuid4().hex[:8]}"
    password = "password123"
    user = User.objects.create_user(username=test_username, password=password)
    
    try:
        now = timezone.now()
        past = now - datetime.timedelta(days=1)
        
        # Create an already unlocked capsule
        Capsule.objects.create(
            user=user,
            title="Old Secrets",
            content="Some secrets",
            mood="nostalgic",
            unlock_date=past,
            created_at=past
        )
        
        # Run check_unlocks command
        print("--- Running check_unlocks (First Time) ---")
        out1 = subprocess.check_output(['python', 'manage.py', 'check_unlocks']).decode('utf-8')
        print(out1.strip())
        
        print("\n--- Running check_unlocks (Second Time) ---")
        out2 = subprocess.check_output(['python', 'manage.py', 'check_unlocks']).decode('utf-8')
        print(out2.strip())
        
        # Get JWT Token
        token_resp = requests.post('http://localhost:8000/api/token/', json={
            'username': test_username,
            'password': password
        })
        token = token_resp.json().get('access')
        
        # Call API
        print("\n--- API Response for GET /api/notifications/ ---")
        resp = requests.get(
            'http://localhost:8000/api/notifications/',
            headers={'Authorization': f'Bearer {token}'}
        )
        print("Status Code:", resp.status_code)
        print("JSON Response:")
        print(resp.json())
        
    finally:
        user.delete()

if __name__ == '__main__':
    run_test()
