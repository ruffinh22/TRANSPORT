"""Serializers pour l'app Parcels"""
from rest_framework import serializers
from .models import Parcel


class ParcelSerializer(serializers.ModelSerializer):
    sender_info = serializers.CharField(source='sender.email', read_only=True)

    class Meta:
        model = Parcel
        fields = [
            'id', 'trip', 'sender', 'sender_info', 'recipient_name',
            'recipient_phone', 'weight', 'price', 'status',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
