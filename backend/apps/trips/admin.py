"""Admin pour l'app Trajets"""
from django.contrib import admin
from .models import Trip


@admin.register(Trip)
class TripAdmin(admin.ModelAdmin):
    list_display = ['id', 'vehicle', 'departure_location', 'arrival_location', 'departure_time', 'status']
    list_filter = ['status', 'departure_time', 'created_at']
    search_fields = ['departure_location', 'arrival_location']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'departure_time'
