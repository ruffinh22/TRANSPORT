"""Serializers pour l'app Trips"""
from rest_framework import serializers
from .models import Trip


class TripSerializer(serializers.ModelSerializer):
    vehicle_info = serializers.CharField(source='vehicle.registration_number', read_only=True)

    class Meta:
        model = Trip
        fields = [
            'id', 'vehicle', 'vehicle_info', 'departure_location',
            'arrival_location', 'departure_time', 'arrival_time',
            'available_seats', 'price_per_seat', 'status',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
