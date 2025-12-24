"""Admin pour l'app Billets"""
from django.contrib import admin
from .models import Ticket


@admin.register(Ticket)
class TicketAdmin(admin.ModelAdmin):
    list_display = ['id', 'trip', 'passenger', 'seat_number', 'status', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['passenger__email', 'trip__id']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
