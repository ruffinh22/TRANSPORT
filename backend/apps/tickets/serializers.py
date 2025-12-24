"""Serializers pour l'app Tickets"""
from rest_framework import serializers
from .models import Ticket


class TicketSerializer(serializers.ModelSerializer):
    passenger_info = serializers.CharField(source='passenger.email', read_only=True)
    trip_info = serializers.CharField(source='trip.id', read_only=True)

    class Meta:
        model = Ticket
        fields = [
            'id', 'trip', 'trip_info', 'passenger', 'passenger_info',
            'seat_number', 'price', 'status', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
