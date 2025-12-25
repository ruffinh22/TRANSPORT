"""Serializers pour l'app Cities"""
from rest_framework import serializers
from .models import City


class CitySerializer(serializers.ModelSerializer):
    """Serializer principal pour les villes"""
    is_operational = serializers.ReadOnlyField()
    trip_count = serializers.IntegerField(read_only=True)
    annual_revenue = serializers.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        read_only=True
    )
    
    class Meta:
        model = City
        fields = [
            'id', 
            'name', 
            'code',
            'address', 
            'region', 
            'population',
            'description',
            'latitude', 
            'longitude',
            'is_hub',
            'has_parking',
            'has_terminal',
            'is_operational',
            'trip_count',
            'annual_revenue',
            'is_active', 
            'created_at', 
            'updated_at'
        ]
        read_only_fields = [
            'id', 
            'is_operational',
            'trip_count',
            'annual_revenue',
            'created_at', 
            'updated_at'
        ]

    def validate_code(self, value):
        """Valide le code de la ville"""
        if not value or len(value.strip()) == 0:
            raise serializers.ValidationError("Le code ne peut pas être vide")
        return value.upper()

    def validate(self, data):
        """Valide les données globales"""
        # Vérifie qu'au moins une infrastructure existe
        if not data.get('is_hub') and not data.get('has_terminal'):
            if not self.instance:  # Nouvelle ville
                raise serializers.ValidationError(
                    "Une ville doit être un hub ou avoir un terminal"
                )
        return data


class CityListSerializer(serializers.ModelSerializer):
    """Serializer pour la liste des villes"""
    is_operational = serializers.ReadOnlyField()
    
    class Meta:
        model = City
        fields = [
            'id',
            'name',
            'code',
            'region',
            'is_hub',
            'is_operational',
            'latitude',
            'longitude'
        ]


class CityDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour une ville"""
    is_operational = serializers.ReadOnlyField()
    trip_count = serializers.IntegerField(read_only=True)
    annual_revenue = serializers.DecimalField(
        max_digits=12, 
        decimal_places=2, 
        read_only=True
    )
    
    class Meta:
        model = City
        fields = '__all__'
        read_only_fields = [
            'id',
            'is_operational',
            'trip_count',
            'annual_revenue',
            'created_at',
            'updated_at'
        ]
