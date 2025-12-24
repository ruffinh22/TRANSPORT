"""Admin pour l'app Véhicules"""
from django.contrib import admin
from .models import Vehicle


@admin.register(Vehicle)
class VehicleAdmin(admin.ModelAdmin):
    list_display = ['registration_number', 'vehicle_type', 'brand', 'model', 'capacity', 'is_active']
    list_filter = ['vehicle_type', 'is_active', 'created_at']
    search_fields = ['registration_number', 'brand', 'model']
    readonly_fields = ['created_at', 'updated_at']
