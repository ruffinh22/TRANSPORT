"""Admin panel pour les modèles communs"""
from django.contrib import admin
from .models import (
    Role, Permission, AuditTrail, SystemLog, 
    Notification, FileStorage, Location
)


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'is_active', 'is_system', 'created_at']
    list_filter = ['is_active', 'is_system', 'created_at']
    search_fields = ['code', 'name']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Informations', {
            'fields': ('code', 'name', 'description', 'is_system')
        }),
        ('Permissions', {
            'fields': ('permissions',)
        }),
        ('Statut', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'deleted_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(Permission)
class PermissionAdmin(admin.ModelAdmin):
    list_display = ['code', 'module', 'name', 'is_active', 'created_at']
    list_filter = ['module', 'is_active', 'created_at']
    search_fields = ['code', 'name']
    readonly_fields = ['created_at', 'updated_at']


@admin.register(AuditTrail)
class AuditTrailAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'model_name', 'action', 'timestamp']
    list_filter = ['action', 'model_name', 'timestamp']
    search_fields = ['object_id', 'user__email', 'model_name']
    readonly_fields = [
        'id', 'user', 'model_name', 'object_id', 'action',
        'old_values', 'new_values', 'ip_address', 'user_agent', 'timestamp'
    ]
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SystemLog)
class SystemLogAdmin(admin.ModelAdmin):
    list_display = ['id', 'level', 'module', 'timestamp']
    list_filter = ['level', 'module', 'timestamp']
    search_fields = ['message', 'module', 'function_name']
    readonly_fields = ['id', 'timestamp']
    date_hierarchy = 'timestamp'
    
    def has_add_permission(self, request):
        return False
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'notification_type', 'is_read', 'created_at']
    list_filter = ['notification_type', 'is_read', 'created_at']
    search_fields = ['user__email', 'title', 'message']
    readonly_fields = ['id', 'created_at', 'read_at']
    date_hierarchy = 'created_at'


@admin.register(FileStorage)
class FileStorageAdmin(admin.ModelAdmin):
    list_display = ['id', 'file_name', 'file_type', 'file_size', 'uploaded_by', 'created_at']
    list_filter = ['file_type', 'is_public', 'created_at']
    search_fields = ['file_name', 'uploaded_by__email']
    readonly_fields = ['id', 'created_at', 'file_size']
    date_hierarchy = 'created_at'


@admin.register(Location)
class LocationAdmin(admin.ModelAdmin):
    list_display = ['name', 'city', 'address', 'is_active', 'created_at']
    list_filter = ['city', 'country', 'is_active', 'created_at']
    search_fields = ['name', 'city', 'address']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Informations', {
            'fields': ('name', 'address', 'city', 'postal_code', 'country')
        }),
        ('Localisation', {
            'fields': ('latitude', 'longitude')
        }),
        ('Contact', {
            'fields': ('phone',)
        }),
        ('Statut', {
            'fields': ('is_active',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'deleted_at'),
            'classes': ('collapse',)
        }),
    )
