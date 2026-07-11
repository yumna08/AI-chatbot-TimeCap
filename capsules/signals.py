import logging
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Capsule
from .ai.ingest import embed_capsule
from .ai.vision import generate_caption

logger = logging.getLogger(__name__)

@receiver(post_save, sender=Capsule)
def capsule_post_save(sender, instance, created, **kwargs):
    try:
        embed_capsule(instance)
    except Exception as e:
        logger.warning(f"[TimeCapsule] Skipping embedding for capsule {instance.id}: {e}")
    # If a photo was attached, attempt to generate an AI caption (synchronous for now)
    try:
        if getattr(instance, 'photo', None) and (not getattr(instance, 'ai_caption', None)):
            # Only proceed if the file has a local path
            photo_field = instance.photo
            if hasattr(photo_field, 'path'):
                caption = generate_caption(photo_field.path)
                if caption:
                    instance.ai_caption = caption
                    instance.save(update_fields=['ai_caption'])
    except Exception as e:
        logger.warning(f"[TimeCapsule] Failed to generate caption for capsule {instance.id}: {e}")
