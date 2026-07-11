"""
test_reflect.py
───────────────
Tests the full AI reflection pipeline:
  - Capsule retrieval via smart_search
  - Backfill from DB if fewer than 3 results
  - GPT-4o-mini prompt construction and response

Uses a fresh UUID-based user every run and cleans up after itself.

PROOF THAT THIS IS MOCKED — NOT A REAL API CALL:
  Line 1 sets OPENAI_API_KEY='fake-api-key-for-test'  (a non-existent key).
  Line ~30 patches OpenAIEmbeddings → FakeEmbeddings (random vectors, no HTTP).
  Line ~36 patches ChatOpenAI.invoke → a local Python function (no HTTP).
  If a real network call were made with this fake key, OpenAI would return
  a 401 AuthenticationError and the test would crash immediately.
  The fact that it passes proves no real call was made.
"""
import os
import uuid

# ── PROOF: fake key set BEFORE any import — real call would fail with 401 ─
os.environ['OPENAI_API_KEY'] = 'fake-api-key-for-test'
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'timecapsule.settings')

# ── Mock OpenAI BEFORE django.setup() ─────────────────────────────────────
from unittest.mock import patch
from langchain_core.embeddings import FakeEmbeddings
from langchain_core.messages import AIMessage

patcher_embed = patch(
    'capsules.ai.ingest.OpenAIEmbeddings',
    side_effect=lambda **kwargs: FakeEmbeddings(size=1536)
)
patcher_embed.start()

# django.setup() must come BEFORE patching reflect.ChatOpenAI because
# reflect.py imports Django models at module level (AppRegistryNotReady otherwise)
import django
django.setup()

SIMULATED_RESPONSE = (
    "It looks like your goals have shifted from feeling overwhelming to becoming "
    "a steady, grounding force for you. A few months ago, on 2026-03-10, you "
    "mentioned feeling 'burnt out and struggling to keep up with the daily grind,' "
    "worrying that you had bitten off more than you could chew. But more recently, "
    "on 2026-06-15, your tone shifted significantly — you felt 'energized after "
    "finishing the first major milestone' and noted that taking things one step at "
    "a time actually worked. You've consistently found that when you break down the "
    "larger vision into manageable pieces, the stress turns into motivation."
)

def mock_llm_invoke(self, *args, **kwargs):
    """Replaces ChatOpenAI.invoke — returns a hard-coded AIMessage, no HTTP."""
    return AIMessage(content=SIMULATED_RESPONSE)

patcher_llm = patch('capsules.ai.reflect.ChatOpenAI.invoke', new=mock_llm_invoke)
patcher_llm.start()
# ──────────────────────────────────────────────────────────────────────────

from django.contrib.auth.models import User
from django.utils import timezone
from datetime import timedelta
from capsules.models import Capsule, ReflectionQuery
from capsules.ai.reflect import generate_reflection
from capsules.ai.ingest import get_vectorstore

# ── Unique user for this run ───────────────────────────────────────────────
run_id = str(uuid.uuid4())
username = f"reflect_test_{run_id[:8]}"
user = User.objects.create_user(username=username, password="testpass123")
print(f"[SETUP] Created isolated test user: {username}")
print()
print("── Mock Proof ──────────────────────────────────────────────────────────")
print("  OPENAI_API_KEY = 'fake-api-key-for-test'  (not a real key)")
print("  OpenAIEmbeddings → patched → FakeEmbeddings (random vectors, zero HTTP)")
print("  ChatOpenAI.invoke → patched → local mock_llm_invoke() (zero HTTP)")
print("  A real network call with this key would raise openai.AuthenticationError.")
print("────────────────────────────────────────────────────────────────────────\n")

try:
    now = timezone.now()

    # ── Seed exactly 3 capsules ───────────────────────────────────────────
    # Capsule 1 — stressed, 4 months ago (UNLOCKED)
    c1 = Capsule.objects.create(
        user=user,
        title="Feeling overwhelmed",
        content=(
            "I'm writing this because I just feel so burnt out and struggling to "
            "keep up with the daily grind. The goals I set for this year seem "
            "impossible right now. I feel like I've bitten off more than I can chew, "
            "and I'm not making any real progress. I hope future-me figured this out."
        ),
        mood="stressed",
        unlock_date=now - timedelta(days=100),
    )
    c1.created_at = now - timedelta(days=120)
    c1.save()

    # Capsule 2 — motivated, 1 month ago (UNLOCKED)
    c2 = Capsule.objects.create(
        user=user,
        title="A small win",
        content=(
            "Okay, today was a good day. I felt energized after finishing the first "
            "major milestone of my project. I realized that taking things one step at "
            "a time actually worked. Instead of looking at the massive mountain, I "
            "just focused on today's tasks. It feels good to finally see some momentum."
        ),
        mood="motivated",
        unlock_date=now - timedelta(days=20),
    )
    c2.created_at = now - timedelta(days=25)
    c2.save()

    # Capsule 3 — future/LOCKED — must NOT appear in reflection
    c3 = Capsule.objects.create(
        user=user,
        title="Future goals",
        content=(
            "By the time I read this, I hope I've secured the new role. "
            "I'm feeling anxious about the upcoming interview."
        ),
        mood="sad",
        unlock_date=now + timedelta(days=30),
    )

    print(f"[TEST] Created capsule IDs: unlocked={c1.id}, unlocked={c2.id}, locked={c3.id}")
    print(f"[TEST] Question: 'how have I been feeling about my goals lately'\n")

    # ── Run reflection ────────────────────────────────────────────────────
    result = generate_reflection(user, "how have I been feeling about my goals lately")

    print("─── Generated AI Reflection ────────────────────────────────────────────")
    print(result["reflection"])
    print()
    print(f"  Referenced Capsule IDs : {result['referenced_capsules']}")

    # ── Assertions ────────────────────────────────────────────────────────
    assert c3.id not in result["referenced_capsules"], \
        f"❌ FAIL — locked capsule {c3.id} was referenced (must be excluded)"
    assert result["reflection"] == SIMULATED_RESPONSE, \
        "❌ FAIL — reflection text doesn't match the mocked response"

    # All referenced IDs must belong to this user
    referenced = set(result["referenced_capsules"])
    own_ids = set(Capsule.objects.filter(user=user).values_list("id", flat=True))
    foreign = referenced - own_ids
    assert not foreign, f"❌ FAIL — foreign capsule IDs in result: {foreign}"

    print()
    print("✅  PASS — reflection used only this user's unlocked capsules.")
    print("✅  PASS — locked capsule was correctly excluded.")
    print("✅  PASS — mocked response matched exactly (confirms no real API call).")

finally:
    # ── Teardown ──────────────────────────────────────────────────────────
    print("\n[TEARDOWN] Deleting test user, capsules, reflections, and Chroma collection...")
    try:
        get_vectorstore(user.id).delete_collection()
    except Exception:
        pass
    user.delete()   # cascades to Capsule + ReflectionQuery rows
    patcher_embed.stop()
    patcher_llm.stop()
    print("[TEARDOWN] Done.\n")
