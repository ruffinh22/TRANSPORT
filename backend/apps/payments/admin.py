"""Admin pour l'app Paiements"""
from django.contrib import admin
from .models import Payment


@admin.register(Payment)
class PaymentAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'amount', 'method', 'status', 'created_at']
    list_filter = ['status', 'method', 'created_at']
    search_fields = ['user__email', 'reference']
    readonly_fields = ['created_at', 'updated_at', 'reference']
    date_hierarchy = 'created_at'
