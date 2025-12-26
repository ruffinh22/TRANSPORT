"""Admin pour l'app Colis"""
from django.contrib import admin
from .models import Parcel, ParcelTracking, ParcelCategory, ParcelInsurance


@admin.register(ParcelCategory)
class ParcelCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'base_price', 'is_fragile', 'requires_signature']
    list_filter = ['is_fragile', 'requires_signature']
    search_fields = ['name', 'description']


@admin.register(Parcel)
class ParcelAdmin(admin.ModelAdmin):
    list_display = ['tracking_number', 'sender', 'recipient_name', 'status', 'priority', 'total_price', 'created_at']
    list_filter = ['status', 'priority', 'is_fragile', 'is_insured', 'created_at']
    search_fields = ['sender__email', 'recipient_name', 'recipient_phone', 'tracking_number']
    readonly_fields = ['tracking_number', 'total_price', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    fieldsets = (
        ('Informations générales', {
            'fields': ('tracking_number', 'trip', 'sender', 'category')
        }),
        ('Destinataire', {
            'fields': ('recipient_name', 'recipient_phone', 'recipient_email')
        }),
        ('Contenu', {
            'fields': ('description', 'weight', 'dimensions', 'is_fragile')
        }),
        ('Tarification', {
            'fields': ('base_price', 'weight_surcharge', 'fragile_fee', 'total_price')
        }),
        ('Statut', {
            'fields': ('status', 'priority', 'delivered_at', 'delivery_notes')
        }),
        ('Assurance', {
            'fields': ('is_insured', 'insurance_value', 'insurance_fee'),
            'classes': ('collapse',)
        }),
        ('Dates', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(ParcelTracking)
class ParcelTrackingAdmin(admin.ModelAdmin):
    list_display = ['parcel', 'status', 'location', 'operator', 'created_at']
    list_filter = ['status', 'created_at']
    search_fields = ['parcel__tracking_number', 'location', 'notes']
    readonly_fields = ['created_at']
    date_hierarchy = 'created_at'


@admin.register(ParcelInsurance)
class ParcelInsuranceAdmin(admin.ModelAdmin):
    list_display = ['name', 'coverage_percentage', 'max_coverage_amount', 'base_fee']
    search_fields = ['name', 'description']
