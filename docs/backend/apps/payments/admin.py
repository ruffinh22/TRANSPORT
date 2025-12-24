# apps/payments/admin.py
# =======================

"""
Administration Django pour les modèles de paiement et FeexPay.
"""

from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from django.db.models import Q, Count
from django.utils import timezone
from decimal import Decimal

from .models import (
    PaymentMethod, Transaction, Wallet, WithdrawalRequest,
    PaymentWebhook, ExchangeRate, PaymentSettings,
    FeexPayProvider, FeexPayTransaction, FeexPayWebhookSignature
)


# ============= FEEXPAY ADMIN =============

@admin.register(FeexPayProvider)
class FeexPayProviderAdmin(admin.ModelAdmin):
    """Administration des fournisseurs FeexPay."""
    
    list_display = (
        'provider_name', 'country_code', 'is_active', 'status_badge',
        'min_amount', 'max_amount', 'fee_percentage', 'success_rate',
        'total_transactions'
    )
    list_filter = (
        'is_active', 'country_code', 'provider_code', 'is_test_mode',
        'created_at'
    )
    search_fields = (
        'provider_code', 'provider_name', 'country_code'
    )
    
    fieldsets = (
        (_('Identifiant'), {
            'fields': ('provider_code', 'provider_name', 'country_code')
        }),
        (_('Configuration'), {
            'fields': ('is_active', 'is_test_mode'),
        }),
        (_('Limites de Montant'), {
            'fields': ('min_amount', 'max_amount'),
            'classes': ('collapse',)
        }),
        (_('Frais'), {
            'fields': ('fee_percentage', 'fee_fixed'),
            'classes': ('collapse',)
        }),
        (_('Devises'), {
            'fields': ('supported_currencies',),
            'classes': ('collapse',)
        }),
        (_('Traitement'), {
            'fields': ('processing_time_seconds', 'description', 'icon_url'),
            'classes': ('collapse',)
        }),
        (_('Statistiques'), {
            'fields': ('total_transactions', 'total_volume', 'success_rate'),
            'classes': ('collapse',)
        }),
        (_('Audit'), {
            'fields': ('created_at', 'updated_at', 'last_sync_at'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = (
        'total_transactions', 'total_volume', 'success_rate',
        'created_at', 'updated_at', 'last_sync_at'
    )
    
    def status_badge(self, obj):
        """Afficher le statut avec couleur."""
        if obj.is_active:
            color = '#28a745'  # Vert
            status = '✓ Actif'
        else:
            color = '#dc3545'  # Rouge
            status = '✗ Inactif'
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            status
        )
    
    status_badge.short_description = _('Statut')
    
    def total_transactions(self, obj):
        """Afficher le nombre total de transactions."""
        count = obj.transactions.count()
        return format_html(
            '<strong>{}</strong> transactions',
            count
        )
    
    total_transactions.short_description = _('Transactions')
    
    actions = ['activate_providers', 'deactivate_providers', 'sync_statistics']
    
    def activate_providers(self, request, queryset):
        """Activer les providers sélectionnés."""
        updated = queryset.update(is_active=True)
        self.message_user(request, f'{updated} providers activés.')
    
    activate_providers.short_description = _('Activer les providers sélectionnés')
    
    def deactivate_providers(self, request, queryset):
        """Désactiver les providers sélectionnés."""
        updated = queryset.update(is_active=False)
        self.message_user(request, f'{updated} providers désactivés.')
    
    deactivate_providers.short_description = _('Désactiver les providers sélectionnés')
    
    def sync_statistics(self, request, queryset):
        """Synchroniser les statistiques."""
        for provider in queryset:
            transactions = provider.transactions.all()
            
            provider.total_transactions = transactions.count()
            provider.total_volume = transactions.filter(
                status='successful'
            ).aggregate(
                total=models.Sum('amount')
            )['total'] or Decimal('0')
            
            successful = transactions.filter(status='successful').count()
            total = transactions.count()
            provider.success_rate = (successful / total * 100) if total > 0 else Decimal('100.00')
            
            provider.last_sync_at = timezone.now()
            provider.save()
        
        self.message_user(request, f'Statistiques mises à jour pour {queryset.count()} providers.')
    
    sync_statistics.short_description = _('Synchroniser les statistiques')


@admin.register(FeexPayTransaction)
class FeexPayTransactionAdmin(admin.ModelAdmin):
    """Administration des transactions FeexPay."""
    
    list_display = (
        'internal_transaction_id', 'user_link', 'provider_link',
        'amount_display', 'status_badge', 'created_at',
        'retry_count'
    )
    list_filter = (
        'status', 'provider__provider_code', 'payment_method',
        'currency', 'created_at', 'retry_count'
    )
    search_fields = (
        'internal_transaction_id', 'feexpay_transaction_id',
        'user__username', 'user__email', 'recipient_phone'
    )
    
    fieldsets = (
        (_('Identifiants'), {
            'fields': (
                'internal_transaction_id', 'feexpay_transaction_id',
                'payment_reference'
            )
        }),
        (_('Utilisateur & Provider'), {
            'fields': ('user', 'provider', 'transaction')
        }),
        (_('Montants'), {
            'fields': ('amount', 'currency', 'fee_amount', 'gross_amount')
        }),
        (_('Paiement'), {
            'fields': (
                'payment_method', 'recipient_phone',
                'recipient_email', 'recipient_account'
            )
        }),
        (_('Statut'), {
            'fields': ('status', 'status_message', 'callback_status')
        }),
        (_('Erreurs'), {
            'fields': ('error_code', 'error_message'),
            'classes': ('collapse',)
        }),
        (_('Timing'), {
            'fields': (
                'created_at', 'initiated_at', 'processed_at',
                'completed_at', 'expires_at'
            ),
            'classes': ('collapse',)
        }),
        (_('Retry'), {
            'fields': ('retry_count', 'last_retry_at'),
            'classes': ('collapse',)
        }),
        (_('Métadonnées'), {
            'fields': ('feexpay_response', 'notes', 'ip_address', 'user_agent'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = (
        'internal_transaction_id', 'feexpay_transaction_id',
        'created_at', 'initiated_at', 'processed_at',
        'completed_at', 'expires_at'
    )
    
    def user_link(self, obj):
        """Lien vers l'utilisateur."""
        url = reverse('admin:accounts_user_change', args=[obj.user.id])
        return format_html(
            '<a href="{}">{}</a>',
            url,
            obj.user.username
        )
    
    user_link.short_description = _('Utilisateur')
    
    def provider_link(self, obj):
        """Lien vers le provider."""
        return format_html(
            '<strong>{}</strong>',
            obj.provider.provider_name
        )
    
    provider_link.short_description = _('Provider')
    
    def amount_display(self, obj):
        """Afficher le montant avec devise."""
        return format_html(
            '{} {}',
            obj.amount,
            obj.currency
        )
    
    amount_display.short_description = _('Montant')
    
    def status_badge(self, obj):
        """Afficher le statut avec couleur."""
        colors = {
            'pending': '#ffc107',
            'processing': '#17a2b8',
            'successful': '#28a745',
            'failed': '#dc3545',
            'cancelled': '#6c757d',
            'expired': '#6c757d',
        }
        color = colors.get(obj.status, '#999999')
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            obj.get_status_display()
        )
    
    status_badge.short_description = _('Statut')
    
    actions = ['mark_successful', 'mark_failed', 'retry_transactions']
    
    def mark_successful(self, request, queryset):
        """Marquer comme réussi."""
        updated = 0
        for tx in queryset:
            if tx.status != 'successful':
                tx.mark_as_successful(tx.feexpay_transaction_id, 'successful')
                updated += 1
        
        self.message_user(request, f'{updated} transactions marquées réussies.')
    
    mark_successful.short_description = _('Marquer comme réussi')
    
    def mark_failed(self, request, queryset):
        """Marquer comme échoué."""
        updated = 0
        for tx in queryset:
            if tx.status != 'failed':
                tx.mark_as_failed('MANUAL', 'Marqué comme échoué manuellement')
                updated += 1
        
        self.message_user(request, f'{updated} transactions marquées échouées.')
    
    mark_failed.short_description = _('Marquer comme échoué')
    
    def retry_transactions(self, request, queryset):
        """Relancer les transactions."""
        updated = 0
        for tx in queryset:
            if tx.can_retry():
                tx.retry()
                updated += 1
        
        self.message_user(request, f'{updated} transactions relancées.')
    
    retry_transactions.short_description = _('Relancer les transactions')


@admin.register(FeexPayWebhookSignature)
class FeexPayWebhookSignatureAdmin(admin.ModelAdmin):
    """Administration des signatures de webhook."""
    
    list_display = (
        'webhook_id_short', 'event_type', 'transaction_link',
        'is_valid_badge', 'is_processed_badge', 'received_at'
    )
    list_filter = (
        'is_valid', 'is_processed', 'event_type', 'received_at',
        'retry_count'
    )
    search_fields = (
        'webhook_id', 'event_type', 'transaction__internal_transaction_id'
    )
    
    fieldsets = (
        (_('Webhook'), {
            'fields': ('webhook_id', 'event_type')
        }),
        (_('Données'), {
            'fields': ('payload', 'headers', 'signature'),
            'classes': ('collapse',)
        }),
        (_('Validation'), {
            'fields': ('is_valid', 'validation_error')
        }),
        (_('Traitement'), {
            'fields': ('is_processed', 'processed_at', 'processing_error')
        }),
        (_('Retry'), {
            'fields': ('retry_count', 'next_retry_at'),
            'classes': ('collapse',)
        }),
        (_('Métadonnées'), {
            'fields': ('ip_address', 'user_agent', 'received_at', 'transaction'),
            'classes': ('collapse',)
        }),
    )
    
    readonly_fields = (
        'webhook_id', 'event_type', 'received_at', 'processed_at'
    )
    
    def webhook_id_short(self, obj):
        """Afficher ID webhook raccourci."""
        return obj.webhook_id[:16] + '...'
    
    webhook_id_short.short_description = _('Webhook ID')
    
    def transaction_link(self, obj):
        """Lien vers la transaction."""
        if obj.transaction:
            url = reverse('admin:payments_feexpaytransaction_change', args=[obj.transaction.id])
            return format_html(
                '<a href="{}">{}</a>',
                url,
                obj.transaction.internal_transaction_id[:20]
            )
        return '–'
    
    transaction_link.short_description = _('Transaction')
    
    def is_valid_badge(self, obj):
        """Afficher validité avec couleur."""
        if obj.is_valid:
            color = '#28a745'
            status = '✓ Valide'
        else:
            color = '#dc3545'
            status = '✗ Invalide'
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            status
        )
    
    is_valid_badge.short_description = _('Validité')
    
    def is_processed_badge(self, obj):
        """Afficher traitement avec couleur."""
        if obj.is_processed:
            color = '#28a745'
            status = '✓ Traité'
        else:
            color = '#ffc107'
            status = '⊘ En attente'
        
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 3px;">{}</span>',
            color,
            status
        )
    
    is_processed_badge.short_description = _('Traitement')
    
    actions = ['mark_as_processed', 'reset_retry', 'delete_old_webhooks']
    
    def mark_as_processed(self, request, queryset):
        """Marquer comme traité."""
        updated = queryset.update(
            is_processed=True,
            processed_at=timezone.now()
        )
        self.message_user(request, f'{updated} webhooks marqués comme traités.')
    
    mark_as_processed.short_description = _('Marquer comme traité')
    
    def reset_retry(self, request, queryset):
        """Réinitialiser les retries."""
        updated = queryset.update(
            retry_count=0,
            next_retry_at=None
        )
        self.message_user(request, f'{updated} webhooks réinitialisés.')
    
    reset_retry.short_description = _('Réinitialiser les retries')
    
    def delete_old_webhooks(self, request, queryset):
        """Supprimer les vieux webhooks traités."""
        threshold = timezone.now() - timezone.timedelta(days=30)
        deleted_count, _ = FeexPayWebhookSignature.objects.filter(
            is_processed=True,
            processed_at__lt=threshold
        ).delete()
        
        self.message_user(request, f'{deleted_count} webhooks anciens supprimés.')
    
    delete_old_webhooks.short_description = _('Supprimer les webhooks > 30j traités')


# ============= EXISTING MODELS ADMIN (keep existing configs) =============

# Vous pouvez ajouter l'admin pour les autres modèles de paiement existants ici
# PaymentMethod, Transaction, Wallet, WithdrawalRequest, etc.
