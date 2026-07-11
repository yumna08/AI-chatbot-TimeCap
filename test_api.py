"""
test_api.py
───────────
Tests the full HTTP flow:
  JWT login → POST /api/capsules/ → raw ChromaDB similarity search

Uses a fresh UUID-based user every run and cleans up after itself.
The server-side signal (embed_capsule) is gracefully skipped when
OPENAI_API_KEY is missing — this is expected and logged server-side.
OpenAI embeddings in this test process are mocked via FakeEmbeddings.
"""
import os
import uuid
import django
import requests

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

from django.utils import timezone
from datetime import timedelta
from django.contrib.auth.models import User
from capsules.models import Capsule
from capsules.ai.ingest import get_vectorstore, embed_capsule

BASE_URL = 'http://127.0.0.1:8001'

# ── Unique user for this run ───────────────────────────────────────────────
run_id = str(uuid.uuid4())
username = f"api_test_{run_id[:8]}"
password = "TestPass1234!"
user = User.objects.create_user(username=username, password=password)
print(f"[SETUP] Created isolated test user: {username}\n")

try:
    # ── Step 1: Login via API ─────────────────────────────────────────────
    print("── Step 1: POST /api/token/ ─────────────────────────────────────────")
    token_resp = requests.post(
        f"{BASE_URL}/api/token/",
        json={"username": username, "password": password},
        timeout=10,
    )
    print(f"  HTTP {token_resp.status_code}  →  {token_resp.text[:120]}")
    assert token_resp.status_code == 200, f"❌ Login failed: {token_resp.text}"
    token = token_resp.json()["access"]
    headers = {"Authorization": f"Bearer {token}"}
    print("  ✅ JWT obtained.\n")

    # ── Step 2: Create capsule via API ────────────────────────────────────
    print("── Step 2: POST /api/capsules/ ──────────────────────────────────────")
    unlock_date = (timezone.now() + timedelta(days=2)).isoformat()
    payload = {
        "title": f"API Test Capsule {run_id}",
        "content": "This capsule was created via the REST API to test the full HTTP flow.",
        "mood": "motivated",
        "unlock_date": unlock_date,
        "tags": ["api", "test", "isolated"],
    }
    create_resp = requests.post(
        f"{BASE_URL}/api/capsules/",
        json=payload,
        headers=headers,
        timeout=10,
    )
    print(f"  HTTP {create_resp.status_code}  →  {create_resp.text[:300]}")
    assert create_resp.status_code == 201, f"❌ Create failed: {create_resp.text}"
    capsule_data = create_resp.json()
    capsule_id = capsule_data["id"]
    print(f"  ✅ Capsule created with ID={capsule_id}\n")

    # ── Step 3: Manually embed in this process (server skipped it, no key) ─
    print("── Step 3: Embed capsule into local ChromaDB (mocked embeddings) ────")
    capsule_obj = Capsule.objects.get(id=capsule_id)
    embed_capsule(capsule_obj)
    print("  ✅ Embedding written to ChromaDB.\n")

    # ── Step 4: Verify in ChromaDB ────────────────────────────────────────
    print("── Step 4: Chroma similarity_search ─────────────────────────────────")
    vectorstore = get_vectorstore(user.id)
    results = vectorstore.similarity_search("REST API full HTTP flow", k=3)
    print(f"  Found {len(results)} result(s).")
    found = False
    for doc in results:
        print(f"  - capsule_id={doc.metadata.get('capsule_id')}  content='{doc.page_content[:60]}...'")
        if doc.metadata.get("capsule_id") == capsule_id:
            found = True
    assert found, f"❌ FAIL — capsule {capsule_id} not found in ChromaDB"
    print("  ✅ Capsule found in ChromaDB.\n")

    # ── Step 5: GET /api/capsules/?include_locked=true ───────────────────
    print("── Step 5: GET /api/capsules/?include_locked=true ───────────────────")
    list_resp = requests.get(
        f"{BASE_URL}/api/capsules/?include_locked=true",
        headers=headers,
        timeout=10,
    )
    print(f"  HTTP {list_resp.status_code}")
    items = list_resp.json()
    print(f"  Returned {len(items)} capsule(s) for this user.")
    assert any(c["id"] == capsule_id for c in items), "❌ FAIL — created capsule not in list"
    print("  ✅ Capsule appears in user's list.\n")

    print("✅  ALL STEPS PASSED — full HTTP flow verified.")

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
