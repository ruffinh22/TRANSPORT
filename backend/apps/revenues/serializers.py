"""Serializers pour l'app Revenues"""
from rest_framework import serializers
from .models import Revenue


class RevenueSerializer(serializers.ModelSerializer):
    class Meta:
        model = Revenue
        fields = [
            'id', 'date', 'total_revenue', 'expenses', 'profit',
            'tickets_count', 'parcels_count', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
