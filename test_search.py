"""
test_search.py
──────────────
Tests that smart_search returns ONLY unlocked capsules,
even when a locked capsule with identical content exists.

Uses a fresh UUID-based user every run and cleans up after itself.
OpenAI is mocked — no real API call is made.
"""
import os
import uuid
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timecapsule.settings')

# ── Mock OpenAI BEFORE django.setup() ─────────────────────────────────────
from unittest.mock import patch
from langchain_core.embeddings import FakeEmbeddings

patcher = patch(
    'capsules.ai.ingest.OpenAIEmbeddings',
    side_effect=lambda **kwargs: FakeEmbeddings(size=1536)
)
patcher.start()
# ──────────────────────────────────────────────────────────────────────────

django.setup()

from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from capsules.models import Capsule
from capsules.ai.search import smart_search
from capsules.ai.ingest import get_vectorstore

# ── Unique user for this run ───────────────────────────────────────────────
run_id = str(uuid.uuid4())
username = f"search_test_{run_id[:8]}"
user = User.objects.create_user(username=username, password="testpass123")
print(f"[SETUP] Created isolated test user: {username}\n")

try:
    now = timezone.now()

    # 1. UNLOCKED capsule (unlock_date in the past)
    unlocked = Capsule.objects.create(
        user=user,
        title="Unlocked capsule — should appear",
        content="This is highly similar content for the search test.",
        mood="happy",
        unlock_date=now - timedelta(days=1),
    )
    print(f"[TEST] Created UNLOCKED capsule  ID={unlocked.id}")

    # 2. LOCKED capsule (unlock_date in the future) — identical content
    locked = Capsule.objects.create(
        user=user,
        title="Locked capsule — must NOT appear",
        content="This is highly similar content for the search test.",
        mood="sad",
        unlock_date=now + timedelta(days=5),
    )
    print(f"[TEST] Created LOCKED capsule    ID={locked.id}")

    # 3. Run smart_search
    query = "similar content search test"
    print(f"\n[TEST] Running smart_search with query: '{query}'")
    results = smart_search(user, query)

    print("\n─── Smart Search Results ───────────────────────────────")
    print(f"  Found {len(results)} result(s).")
    returned_ids = []
    for res in results:
        print(f"  - ID={res['capsule_id']}  title='{res['title']}'  unlock_date={res['unlock_date']}")
        returned_ids.append(res["capsule_id"])

    # 4. Assertions
    assert unlocked.id in returned_ids, f"❌ FAIL — unlocked capsule {unlocked.id} missing from results"
    assert locked.id not in returned_ids, f"❌ FAIL — locked capsule {locked.id} appeared in results (should be hidden)"
    assert len(results) == 1, f"❌ FAIL — expected exactly 1 result for this user, got {len(results)}"

    print("\n✅  PASS — only the unlocked capsule appeared; locked capsule was correctly hidden.")

finally:
    # ── Teardown ──────────────────────────────────────────────────────────
    print("\n[TEARDOWN] Deleting test user, capsules, and Chroma collection...")
    try:
        get_vectorstore(user.id).delete_collection()
    except Exception:
        pass
    user.delete()
    patcher.stop()
    print("[TEARDOWN] Done.\n")
