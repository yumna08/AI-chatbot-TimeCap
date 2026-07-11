# capsules/management/commands/clean_chroma.py
"""
Management command that removes stale ChromaDB collections which no longer
correspond to a real Django ``User``.

Usage
-----
    # Dry‑run (default) – just shows what would be deleted
    python manage.py clean_chroma

    # Actual deletion – confirm with the flag
    python manage.py clean_chroma --confirm
"""

import re
from pathlib import Path

from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from django.conf import settings

# Chroma persistent client – points at the folder defined in settings or
# at the default location ``BASE_DIR / "chroma_db"``.
from chromadb import PersistentClient

User = get_user_model()


class Command(BaseCommand):
    help = (
        "Deletes Chroma collections that are not linked to any existing User. "
        "Runs as a dry‑run unless '--confirm' is supplied."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--confirm",
            action="store_true",
            help=(
                "Actually delete the orphaned collections. If omitted the command "
                "only prints what would be removed."
            ),
        )

    def handle(self, *args, **options):
        # --------------------------------------------------------------------
        # 1️⃣ Determine where the Chroma DB lives
        # --------------------------------------------------------------------
        db_path = getattr(settings, "CHROMA_DB_PATH", None)
        if not db_path:
            # Default path used by the project (see settings.py)
            db_path = Path(settings.BASE_DIR) / "chroma_db"
        db_path = Path(db_path).resolve()
        self.stdout.write(f"🔎 Scanning Chroma folder: {db_path}")

        if not db_path.is_dir():
            self.stderr.write(self.style.ERROR("❌ Chroma folder does not exist."))
            return

        # --------------------------------------------------------------------
        # 2️⃣ Build a set of valid collection names: "user_{id}"
        # --------------------------------------------------------------------
        valid_names = {f"user_{user.id}" for user in User.objects.all()}
        self.stdout.write(f"✅ Found {len(valid_names)} real user collection(s).")

        # --------------------------------------------------------------------
        # 3️⃣ List every collection present on disk
        # --------------------------------------------------------------------
        client = PersistentClient(path=str(db_path))
        all_collections = {col.name for col in client.list_collections()}

        # Any name not matching the pattern is considered orphaned.
        pattern = re.compile(r"^user_\d+$")
        orphaned = {
            name for name in all_collections if not pattern.fullmatch(name) or name not in valid_names
        }

        # --------------------------------------------------------------------
        # 4️⃣ Report what would happen (dry‑run)
        # --------------------------------------------------------------------
        if not orphaned:
            self.stdout.write(self.style.SUCCESS("✅ No orphaned collections found."))
            return

        self.stdout.write("\n=== DRY‑RUN SUMMARY ===")
        self.stdout.write("🗑️  Orphaned collections (will be removed):")
        for name in sorted(orphaned):
            self.stdout.write(f"   - {name}")

        # --------------------------------------------------------------------
        # 5️⃣ If --confirm, actually delete them
        # --------------------------------------------------------------------
        if not options["confirm"]:
            self.stdout.write(
                self.style.WARNING(
                    "\n⚠️  No deletions performed. Rerun with '--confirm' to delete the above collections."
                )
            )
            return

        self.stdout.write("\n🚀 Performing deletion…")
        for name in sorted(orphaned):
            try:
                client.delete_collection(name)
                self.stdout.write(self.style.SUCCESS(f"✔ Deleted: {name}"))
            except Exception as exc:  # pragma: no‑cover – defensive
                self.stderr.write(self.style.ERROR(f"Failed to delete {name}: {exc}"))

        self.stdout.write(self.style.SUCCESS("\n✅ Cleanup complete."))
