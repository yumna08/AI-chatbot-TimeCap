import os
import django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timecapsule.settings')
django.setup()

import datetime
from django.utils import timezone
from django.contrib.auth.models import User
from capsules.models import Capsule
from rest_framework.test import APIClient
import uuid

def run_test():
    # 1. Create a fresh isolated test user
    test_username = f"testuser_{uuid.uuid4().hex[:8]}"
    user = User.objects.create_user(username=test_username, password="password")
    
    try:
        # 2. Seed capsules across different months and moods
        now = timezone.now()
        
        # Month 1: 2 stressed, 1 motivated (all unlocked)
        month1 = now - datetime.timedelta(days=60)
        c1 = Capsule.objects.create(user=user, title="S1", content="c", mood="stressed", unlock_date=month1)
        c2 = Capsule.objects.create(user=user, title="S2", content="c", mood="stressed", unlock_date=month1)
        c3 = Capsule.objects.create(user=user, title="M1", content="c", mood="motivated", unlock_date=month1)
        Capsule.objects.filter(id__in=[c1.id, c2.id, c3.id]).update(created_at=month1)
        
        # Month 2: 2 motivated (unlocked), 1 happy (LOCKED - should be excluded)
        month2 = now - datetime.timedelta(days=20)
        c4 = Capsule.objects.create(user=user, title="M2", content="c", mood="motivated", unlock_date=month2)
        c5 = Capsule.objects.create(user=user, title="M3", content="c", mood="motivated", unlock_date=month2)
        
        # Locked capsule in month 2 (unlock_date in the future)
        future = now + datetime.timedelta(days=10)
        c6 = Capsule.objects.create(user=user, title="H1", content="c", mood="happy", unlock_date=future)
        Capsule.objects.filter(id__in=[c4.id, c5.id, c6.id]).update(created_at=month2)
        
        # 3. Call the endpoint
        client = APIClient(SERVER_NAME='localhost')
        client.force_authenticate(user=user)
        response = client.get('/api/capsules/mood-trends/')
        
        # 4. Print and assert results
        print("Status Code:", response.status_code)
        data = response.json()
        print("Response Data:", data)
        
        m1_key = month1.strftime('%Y-%m')
        m2_key = month2.strftime('%Y-%m')
        
        assert data.get(m1_key, {}).get("stressed") == 2, f"Expected 2 stressed in {m1_key}"
        assert data.get(m1_key, {}).get("motivated") == 1, f"Expected 1 motivated in {m1_key}"
        assert data.get(m2_key, {}).get("motivated") == 2, f"Expected 2 motivated in {m2_key}"
        assert "happy" not in data.get(m2_key, {}), "Locked capsule should be excluded"
        
        print("\nTest passed successfully!")
        
    finally:
        # Cleanup
        user.delete()

if __name__ == "__main__":
    run_test()
