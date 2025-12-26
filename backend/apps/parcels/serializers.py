"""Serializers pour l'app Parcels"""
from rest_framework import serializers
from .models import Parcel, ParcelTracking, ParcelCategory, ParcelInsurance


class ParcelCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = ParcelCategory
        fields = ['id', 'name', 'description', 'base_price', 'is_fragile', 'requires_signature']


class ParcelTrackingSerializer(serializers.ModelSerializer):
    operator_name = serializers.CharField(source='operator.get_full_name', read_only=True)
    
    class Meta:
        model = ParcelTracking
        fields = [
            'id', 'parcel', 'status', 'location', 'notes', 'operator',
            'operator_name', 'created_at'
        ]
        read_only_fields = ['id', 'created_at']


class ParcelInsuranceSerializer(serializers.ModelSerializer):
    class Meta:
        model = ParcelInsurance
        fields = [
            'id', 'name', 'description', 'coverage_percentage',
            'max_coverage_amount', 'base_fee'
        ]


class ParcelListSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.get_full_name', read_only=True)
    trip_number = serializers.CharField(source='trip.number', read_only=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    
    class Meta:
        model = Parcel
        fields = [
            'id', 'tracking_number', 'sender', 'sender_name', 'trip_number',
            'recipient_name', 'weight', 'total_price', 'status', 'priority',
            'is_fragile', 'created_at'
        ]
        read_only_fields = ['id', 'tracking_number', 'created_at']


class ParcelDetailSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.get_full_name', read_only=True)
    trip_info = serializers.SerializerMethodField()
    category_info = ParcelCategorySerializer(source='category', read_only=True)
    tracking_history = ParcelTrackingSerializer(many=True, read_only=True)
    
    class Meta:
        model = Parcel
        fields = [
            'id', 'tracking_number', 'sender', 'sender_name', 'trip', 'trip_info',
            'category', 'category_info', 'recipient_name', 'recipient_phone',
            'recipient_email', 'description', 'weight', 'dimensions',
            'base_price', 'weight_surcharge', 'fragile_fee', 'total_price',
            'status', 'priority', 'is_fragile', 'requires_signature',
            'delivered_at', 'delivery_notes', 'is_insured', 'insurance_value',
            'insurance_fee', 'tracking_history', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'tracking_number', 'total_price', 'created_at', 'updated_at']
    
    def get_trip_info(self, obj):
        from apps.trips.serializers import TripListSerializer
        return TripListSerializer(obj.trip).data


class ParcelCreateUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parcel
        fields = [
            'trip', 'sender', 'category', 'recipient_name', 'recipient_phone',
            'recipient_email', 'description', 'weight', 'dimensions',
            'base_price', 'weight_surcharge', 'fragile_fee', 'priority',
            'is_fragile', 'requires_signature', 'is_insured', 'insurance_value',
            'insurance_fee'
        ]
    
    def validate(self, data):
        """Valide les données du colis"""
        if data['weight'] <= 0:
            raise serializers.ValidationError("Le poids doit être supérieur à 0")
        
        if data['base_price'] < 0:
            raise serializers.ValidationError("Le prix ne peut pas être négatif")
        
        if data.get('insurance_value', 0) > 0 and not data.get('is_insured'):
            raise serializers.ValidationError("Vous devez cocher 'Assuré' pour définir une valeur d'assurance")
        
        return data


class ParcelStatisticsSerializer(serializers.Serializer):
    """Statistiques sur les colis"""
    total_parcels = serializers.IntegerField()
    pending_parcels = serializers.IntegerField()
    delivered_parcels = serializers.IntegerField()
    lost_parcels = serializers.IntegerField()
    total_revenue = serializers.DecimalField(max_digits=12, decimal_places=2)
    average_price = serializers.DecimalField(max_digits=10, decimal_places=2)
    total_weight = serializers.DecimalField(max_digits=12, decimal_places=2)
    fragile_parcels = serializers.IntegerField()
