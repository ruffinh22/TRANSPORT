"""Signaux Django pour les modèles communs"""
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import AuditTrail
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=AuditTrail)
def log_audit_trail(sender, instance, created, **kwargs):
    """Logger l'audit trail dans le système de log"""
    if created:
        logger.info(
            f"Audit: {instance.model_name}({instance.object_id}) - "
            f"{instance.action} by {instance.user}",
            extra={
                'model': instance.model_name,
                'action': instance.action,
                'user_id': instance.user_id if instance.user else None,
            }
        )
