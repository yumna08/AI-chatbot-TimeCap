import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Capsule
from .ai.ingest import embed_capsule

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Capsule)
def capsule_post_save(sender, instance, created, **kwargs):
    try:
        embed_capsule(instance)
    except Exception as e:
        logger.warning(f"[TimeCapsule] Skipping embedding for capsule {instance.id}: {e}")
