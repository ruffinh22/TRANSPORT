"""Admin panel pour les utilisateurs"""
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, UserSession


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = [
        'email', 'get_full_name', 'phone', 'is_active', 'is_blocked',
        'is_fully_verified', 'created_at'
    ]
    list_filter = [
        'is_active', 'is_blocked', 'email_verified',
        'phone_verified', 'document_verified', 'created_at'
    ]
    search_fields = ['email', 'phone', 'first_name', 'last_name']
    ordering = ['-created_at']
    readonly_fields = ['created_at', 'updated_at', 'last_login']
    
    fieldsets = (
        ('Authentification', {
            'fields': ('email', 'password', 'phone')
        }),
        ('Profil Personnel', {
            'fields': (
                'first_name', 'last_name', 'date_of_birth', 'gender',
                'avatar'
            )
        }),
        ('Identité Légale', {
            'fields': (
                'document_type', 'document_number', 'document_issue_date',
                'document_expiry_date', 'document_photo', 'document_verified',
                'document_verified_at', 'document_verified_by'
            ),
            'classes': ('collapse',)
        }),
        ('Localisation', {
            'fields': ('country', 'city', 'address', 'postal_code')
        }),
        ('Profil Entreprise', {
            'fields': (
                'employee_id', 'company_name', 'company_registration'
            ),
            'classes': ('collapse',)
        }),
        ('Bancaire', {
            'fields': ('bank_name', 'bank_account', 'bank_code'),
            'classes': ('collapse',)
        }),
        ('Préférences', {
            'fields': (
                'language', 'timezone',
                'notify_email', 'notify_sms', 'notify_push'
            )
        }),
        ('Vérifications', {
            'fields': (
                'email_verified', 'email_verified_at',
                'phone_verified', 'phone_verified_at'
            )
        }),
        ('Sécurité', {
            'fields': (
                'is_active', 'is_blocked', 'block_reason', 'blocked_at',
                'is_staff', 'is_superuser',
                'last_login_ip', 'last_login_device',
                'failed_login_attempts', 'locked_until'
            )
        }),
        ('Rôles et Permissions', {
            'fields': ('roles', 'groups'),
            'classes': ('collapse',)
        }),
        ('Termes et Conditions', {
            'fields': ('accepted_terms_at', 'accepted_privacy_at'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at', 'deleted_at', 'last_login'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('email', 'phone', 'first_name', 'last_name', 'password1', 'password2'),
        }),
    )
    
    def get_full_name(self, obj):
        return obj.get_full_name()
    get_full_name.short_description = 'Nom Complet'
    
    def is_fully_verified(self, obj):
        return obj.is_fully_verified
    is_fully_verified.boolean = True
    is_fully_verified.short_description = 'Entièrement Vérifié'


@admin.register(UserSession)
class UserSessionAdmin(admin.ModelAdmin):
    list_display = ['user', 'device_name', 'ip_address', 'is_active', 'expires_at']
    list_filter = ['is_active', 'created_at', 'expires_at']
    search_fields = ['user__email', 'device_name', 'ip_address']
    readonly_fields = ['created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Utilisateur', {
            'fields': ('user',)
        }),
        ('Session', {
            'fields': ('refresh_token', 'device_name', 'user_agent')
        }),
        ('Accès', {
            'fields': ('ip_address', 'is_active')
        }),
        ('Dates', {
            'fields': ('expires_at', 'logged_out_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
