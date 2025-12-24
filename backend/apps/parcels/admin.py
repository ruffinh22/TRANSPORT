"""Admin pour l'app Colis"""
from django.contrib import admin
from .models import Parcel


@admin.register(Parcel)
class ParcelAdmin(admin.ModelAdmin):
    list_display = ['id', 'trip', 'sender', 'recipient_name', 'weight', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['sender__email', 'recipient_name', 'recipient_phone']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
