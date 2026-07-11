"""
test_embedding.py
─────────────────
Tests that saving a Capsule triggers the post_save signal
and auto-embeds it into ChromaDB.

Uses a fresh UUID-based user every run and cleans up after itself.
OpenAI is mocked — no real API call is made.
"""
import os
import uuid
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timecapsule.settings')

# ── Mock OpenAI BEFORE django.setup() loads any app code ──────────────────
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
from capsules.ai.ingest import get_vectorstore

# ── Unique user for this run ───────────────────────────────────────────────
run_id = str(uuid.uuid4())
username = f"embed_test_{run_id[:8]}"
user = User.objects.create_user(username=username, password="testpass123")
print(f"[SETUP] Created isolated test user: {username}")

try:
    # 1. Create a capsule — triggers post_save → embed_capsule()
    capsule = Capsule.objects.create(
        user=user,
        title=f"Embedding Test Capsule {run_id}",
        content="This is the content of my test capsule for LangChain and Chroma.",
        mood="happy",
        unlock_date=timezone.now() + timedelta(days=1),
    )
    print(f"\n[TEST] Created Capsule ID: {capsule.id}")

    # 2. Verify it landed in ChromaDB
    vectorstore = get_vectorstore(user.id)
    results = vectorstore.similarity_search("test capsule", k=1)

    print("\n─── Chroma Search Results ──────────────────────────────")
    if results:
        doc = results[0]
        print(f"  Page Content : {doc.page_content}")
        print(f"  Metadata     : {doc.metadata}")
        assert doc.metadata.get("capsule_id") == capsule.id, "Capsule ID mismatch!"
        print("\n✅  PASS — capsule was embedded and retrieved correctly.")
    else:
        print("❌  FAIL — no results found in ChromaDB.")

finally:
    # ── Teardown ──────────────────────────────────────────────────────────
    print("\n[TEARDOWN] Deleting test user, capsules, and Chroma collection...")
    try:
        get_vectorstore(user.id).delete_collection()
    except Exception:
        pass
    user.delete()   # cascades to Capsule rows
    patcher.stop()
    print("[TEARDOWN] Done.\n")
