"""Serializers pour l'app Reports"""
from rest_framework import serializers
from apps.common.models import AuditTrail


class AuditTrailSerializer(serializers.ModelSerializer):
    """Serializer pour les audit trails"""
    user_email = serializers.EmailField(source='user.email', read_only=True)
    
    class Meta:
        model = AuditTrail
        fields = [
            'id',
            'user',
            'user_email',
            'model_name',
            'object_id',
            'action',
            'old_values',
            'new_values',
            'ip_address',
            'user_agent',
            'timestamp',
        ]
        read_only_fields = [
            'id',
            'timestamp',
        ]
