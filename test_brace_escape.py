"""
Test: Curly-brace escaping in generate_reflection's prompt template.

Approach:
  - Seed a capsule whose content contains literal {curly braces}.
  - Call generate_reflection with a question that also contains braces.
  - Instead of hitting OpenAI, intercept the final rendered prompt string
    and assert:
      1. No KeyError / ValueError is raised during template formatting.
      2. The rendered string contains single braces (not doubled {{ or }}).
"""

import os
os.environ["OPENAI_API_KEY"] = "fake-key-for-test"   # prevents OpenAI init error
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "timecapsule.settings")

import django
django.setup()

import uuid
from datetime import timedelta
from unittest.mock import patch, MagicMock

from django.utils import timezone
from django.contrib.auth.models import User

from capsules.models import Capsule
from langchain_core.embeddings import FakeEmbeddings

# ── Mocks ────────────────────────────────────────────────────────────────────
# 1. Fake embeddings so Chroma doesn't call OpenAI
patch("capsules.ai.ingest.OpenAIEmbeddings",
      side_effect=lambda **kw: FakeEmbeddings(size=1536)).start()

# 2. Intercept ChatOpenAI.invoke to capture the rendered messages
captured_prompt_text = {}

def capturing_invoke(self, messages, **kwargs):
    # `messages` here is the rendered list of BaseMessage objects
    # Join their content so we can inspect the final string sent to the LLM
    full_text = "\n".join(m.content for m in messages)
    captured_prompt_text["value"] = full_text
    mock_msg = MagicMock()
    mock_msg.content = "This is a mock reflection."
    return mock_msg

patch("capsules.ai.reflect.ChatOpenAI.invoke", new=capturing_invoke).start()
# ─────────────────────────────────────────────────────────────────────────────

from capsules.ai.reflect import generate_reflection

# ── Setup ────────────────────────────────────────────────────────────────────
user, _ = User.objects.get_or_create(username="bracetest", email="brace@test.com")
if not user.has_usable_password():
    user.set_password("bracepass")
    user.save()

# Capsule with literal curly braces in content
brace_capsule = Capsule.objects.create(
    user=user,
    title=f"Brace capsule {uuid.uuid4()}",
    content='I felt like {this whole plan} was pointless, almost like {nothing} mattered.',
    mood="stressed",
    unlock_date=timezone.now() - timedelta(days=1),   # already unlocked
)
print(f"Created capsule {brace_capsule.id!r} with braces in content.")

# Question with braces
question = "Why did {this} feel so hard? Was {anything} worth it?"
print(f"Question: {question!r}")

# ── Run ───────────────────────────────────────────────────────────────────────
try:
    result = generate_reflection(user, question)
except (KeyError, ValueError) as e:
    print(f"\n❌ FAIL — template raised {type(e).__name__}: {e}")
    raise SystemExit(1)

# ── Assertions ────────────────────────────────────────────────────────────────
rendered = captured_prompt_text.get("value", "")

# 1. Single braces should appear in the rendered LLM input (not doubled)
assert "{this whole plan}" in rendered, (
    "FAIL: single-brace content not found in rendered prompt.\n"
    f"Rendered prompt:\n{rendered}"
)
assert "{nothing}" in rendered, (
    "FAIL: single-brace '{nothing}' not found in rendered prompt."
)
assert "{this}" in rendered, (
    "FAIL: single-brace '{this}' not found in rendered prompt (from question)."
)
assert "{anything}" in rendered, (
    "FAIL: single-brace '{anything}' not found in rendered prompt (from question)."
)

# 2. Doubled braces must NOT remain in the rendered output
assert "{{" not in rendered, "FAIL: doubled '{{' leaked into rendered prompt."
assert "}}" not in rendered, "FAIL: doubled '}}' leaked into rendered prompt."

print("\n✅ PASS — No KeyError raised.")
print("✅ PASS — Single braces appear correctly in the rendered LLM input.")
print("✅ PASS — No doubled braces leaked through.")
print(f"\nRelevant excerpt from rendered prompt:")
# Print the lines containing our brace content for visual confirmation
for line in rendered.splitlines():
    if "{this" in line or "{nothing" in line or "{anything" in line:
        print(f"  > {line}")
