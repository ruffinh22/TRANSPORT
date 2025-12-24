"""Serializers pour l'app Vehicles"""
from rest_framework import serializers
from .models import Vehicle


class VehicleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Vehicle
        fields = [
            'id', 'registration_number', 'vehicle_type', 'brand', 'model',
            'year', 'capacity', 'plate_number', 'vin', 'is_active',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
