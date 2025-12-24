"""Signaux pour les modèles utilisateurs"""
from django.db.models.signals import post_save
from django.dispatch import receiver
from apps.common.models import AuditTrail
from .models import User, UserSession
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=User)
def audit_user_changes(sender, instance, created, **kwargs):
    """Auditer les changements utilisateurs"""
    if created:
        AuditTrail.objects.create(
            user=instance,
            model_name='User',
            object_id=str(instance.id),
            action='CREATE',
            new_values={'email': instance.email}
        )
