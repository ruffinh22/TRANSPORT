"""Admin pour l'app Revenus"""
from django.contrib import admin
from .models import Revenue


@admin.register(Revenue)
class RevenueAdmin(admin.ModelAdmin):
    list_display = ['date', 'total_revenue', 'profit', 'tickets_count', 'parcels_count']
    list_filter = ['date']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'date'
