# apps/payments/feexpay_serializers.py
# =====================================

"""
Serializers DRF pour FeexPay API.
Supporte l'initiation de paiements, statut, webhooks.
"""

from decimal import Decimal
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.exceptions import ValidationError

from .models import (
    FeexPayProvider, FeexPayTransaction, FeexPayWebhookSignature, Transaction
)
from .feexpay_client import FeexPayClient, FeexPayValidationError, FeexPayAPIError
from apps.accounts.models import User


class FeexPayProviderSerializer(serializers.ModelSerializer):
    """Serializer pour les fournisseurs FeexPay."""
    
    provider_display = serializers.CharField(
        source='get_provider_code_display',
        read_only=True
    )
    country_display = serializers.CharField(
        source='get_country_code_display',
        read_only=True
    )
    fees_info = serializers.SerializerMethodField()
    limits_info = serializers.SerializerMethodField()
    
    class Meta:
        model = FeexPayProvider
        fields = [
            'id', 'provider_code', 'provider_display', 'provider_name',
            'country_code', 'country_display', 'is_active', 'is_test_mode',
            'min_amount', 'max_amount', 'supported_currencies',
            'processing_time_seconds', 'description', 'icon_url',
            'success_rate', 'fees_info', 'limits_info'
        ]
        read_only_fields = [
            'id', 'provider_display', 'country_display', 'success_rate',
            'fees_info', 'limits_info'
        ]
    
    def get_fees_info(self, obj):
        """Détail des frais."""
        return {
            'percentage': float(obj.fee_percentage),
            'fixed': float(obj.fee_fixed),
            'description': _('Frais appliqués sur le montant brut')
        }
    
    def get_limits_info(self, obj):
        """Limites de montant."""
        return {
            'minimum': float(obj.min_amount),
            'maximum': float(obj.max_amount),
            'currencies': obj.supported_currencies
        }


class FeexPayInitiatePaymentSerializer(serializers.Serializer):
    """Serializer pour initier un paiement FeexPay."""
    
    provider_code = serializers.CharField(
        max_length=50,
        help_text=_('Code du fournisseur: mtn, orange, wave, etc.')
    )
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0.01'),
        help_text=_('Montant en devises locale ou EUR/USD')
    )
    currency = serializers.CharField(
        max_length=5,
        default='XOF',
        help_text=_('Devise: XOF (défaut), EUR, USD')
    )
    recipient_phone = serializers.CharField(
        max_length=20,
        required=False,
        allow_blank=True,
        help_text=_('Numéro de téléphone du destinataire')
    )
    recipient_email = serializers.EmailField(
        required=False,
        allow_blank=True,
        help_text=_('Email du destinataire')
    )
    recipient_account = serializers.CharField(
        max_length=255,
        required=False,
        allow_blank=True,
        help_text=_('Compte bancaire ou portefeuille')
    )
    description = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text=_('Description du paiement')
    )
    metadata = serializers.JSONField(
        required=False,
        allow_null=True,
        help_text=_('Métadonnées additionnelles')
    )
    callback_url = serializers.URLField(
        required=False,
        allow_blank=True,
        help_text=_('URL pour les webhooks')
    )
    
    def validate_amount(self, value):
        """Valider le montant."""
        if value <= Decimal('0'):
            raise serializers.ValidationError(_('Montant doit être positif'))
        return value
    
    def validate_currency(self, value):
        """Valider la devise."""
        valid_currencies = ['XOF', 'EUR', 'USD']
        if value.upper() not in valid_currencies:
            raise serializers.ValidationError(
                f"Devise non supportée. Valeurs acceptées: {', '.join(valid_currencies)}"
            )
        return value.upper()
    
    def validate(self, data):
        """Validation croisée."""
        provider_code = data.get('provider_code')
        amount = data.get('amount')
        currency = data.get('currency')
        
        try:
            client = FeexPayClient()
            
            # Valider le fournisseur
            if provider_code not in client.get_supported_providers():
                raise serializers.ValidationError({
                    'provider_code': f'Fournisseur non supporté: {provider_code}'
                })
            
            # Valider le montant
            client.validate_provider_amount(provider_code, amount, currency)
        
        except FeexPayValidationError as e:
            raise serializers.ValidationError(str(e))
        except Exception as e:
            raise serializers.ValidationError(f'Erreur validation: {str(e)}')
        
        return data


class FeexPayTransactionSerializer(serializers.ModelSerializer):
    """Serializer pour les transactions FeexPay."""
    
    provider_display = serializers.CharField(
        source='provider.get_provider_code_display',
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    user_username = serializers.CharField(
        source='user.username',
        read_only=True
    )
    fees_breakdown = serializers.SerializerMethodField()
    can_retry = serializers.SerializerMethodField()
    
    class Meta:
        model = FeexPayTransaction
        fields = [
            'id', 'internal_transaction_id', 'feexpay_transaction_id',
            'user', 'user_username', 'provider', 'provider_display',
            'amount', 'currency', 'payment_method',
            'recipient_phone', 'recipient_email', 'recipient_account',
            'status', 'status_display', 'status_message',
            'fee_amount', 'gross_amount',
            'payment_reference', 'callback_status',
            'error_code', 'error_message',
            'created_at', 'initiated_at', 'processed_at', 'completed_at', 'expires_at',
            'retry_count', 'notes',
            'fees_breakdown', 'can_retry'
        ]
        read_only_fields = [
            'id', 'feexpay_transaction_id', 'provider_display',
            'status_display', 'user_username', 'fees_breakdown', 'can_retry',
            'initiated_at', 'processed_at', 'completed_at', 'expires_at'
        ]
    
    def get_fees_breakdown(self, obj):
        """Détail des frais."""
        return {
            'fee_amount': float(obj.fee_amount),
            'gross_amount': float(obj.gross_amount),
            'percentage_fee': float(obj.fee_amount * (obj.amount / (obj.amount + obj.fee_amount)))
            if obj.amount > 0 else 0
        }
    
    def get_can_retry(self, obj):
        """Vérifier si peut être relancé."""
        return obj.can_retry()


class FeexPayTransactionDetailSerializer(FeexPayTransactionSerializer):
    """Serializer détaillé pour une transaction FeexPay."""
    
    feexpay_response = serializers.JSONField(read_only=True)
    ip_address = serializers.CharField(read_only=True)
    user_agent = serializers.CharField(read_only=True)
    
    class Meta(FeexPayTransactionSerializer.Meta):
        fields = FeexPayTransactionSerializer.Meta.fields + [
            'feexpay_response', 'ip_address', 'user_agent'
        ]


class FeexPayStatusSerializer(serializers.Serializer):
    """Serializer pour vérifier le statut d'un paiement."""
    
    transaction_id = serializers.CharField(
        max_length=255,
        help_text=_('ID de transaction FeexPay')
    )


class FeexPayWebhookPayloadSerializer(serializers.Serializer):
    """Serializer pour valider une charge utile de webhook."""
    
    event = serializers.CharField(max_length=100)
    transaction_id = serializers.CharField(max_length=255)
    status = serializers.CharField(max_length=50)
    timestamp = serializers.DateTimeField()
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False
    )
    currency = serializers.CharField(
        max_length=5,
        required=False
    )
    metadata = serializers.JSONField(required=False)
    error_code = serializers.CharField(
        max_length=100,
        required=False,
        allow_blank=True
    )
    error_message = serializers.CharField(
        required=False,
        allow_blank=True
    )


class FeexPayWebhookHandlerSerializer(serializers.ModelSerializer):
    """Serializer pour traiter les webhooks FeexPay."""
    
    class Meta:
        model = FeexPayWebhookSignature
        fields = [
            'id', 'webhook_id', 'event_type', 'payload',
            'is_valid', 'is_processed', 'transaction',
            'received_at', 'processed_at'
        ]
        read_only_fields = [
            'id', 'is_valid', 'is_processed', 'processed_at', 'received_at'
        ]


class FeexPayPaymentMethodListSerializer(serializers.Serializer):
    """Serializer pour lister les méthodes de paiement disponibles."""
    
    country_code = serializers.CharField(
        max_length=2,
        required=False,
        help_text=_('Filtrer par code pays: SN, CI, TG, etc.')
    )
    active_only = serializers.BooleanField(
        default=True,
        help_text=_('Retourner uniquement les méthodes actives')
    )
    
    def validate_country_code(self, value):
        """Valider le code pays."""
        if value:
            valid_countries = ['SN', 'CI', 'TG', 'BJ', 'GW', 'CM', 'GA']
            if value.upper() not in valid_countries:
                raise serializers.ValidationError(
                    f'Code pays invalide: {value}. Valeurs acceptées: {", ".join(valid_countries)}'
                )
        return value.upper() if value else None


class FeexPayRetryTransactionSerializer(serializers.Serializer):
    """Serializer pour relancer une transaction."""
    
    transaction_id = serializers.CharField(
        max_length=255,
        help_text=_('ID de transaction interne')
    )
    reason = serializers.CharField(
        max_length=500,
        required=False,
        allow_blank=True,
        help_text=_('Raison de la nouvelle tentative')
    )


class FeexPayRefundSerializer(serializers.Serializer):
    """Serializer pour rembourser un paiement."""
    
    transaction_id = serializers.CharField(
        max_length=255,
        help_text=_('ID de transaction FeexPay')
    )
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        required=False,
        help_text=_('Montant à rembourser (total si non spécifié)')
    )
    reason = serializers.CharField(
        max_length=500,
        required=False,
        help_text=_('Raison du remboursement')
    )


class FeexPayExchangeRateSerializer(serializers.Serializer):
    """Serializer pour les taux de change."""
    
    base_currency = serializers.CharField(
        max_length=5,
        default='XOF',
        help_text=_('Devise de référence')
    )
    from_currency = serializers.CharField(
        max_length=5,
        help_text=_('Devise source')
    )
    to_currency = serializers.CharField(
        max_length=5,
        help_text=_('Devise cible')
    )
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        help_text=_('Montant à convertir')
    )


class FeexPayStatisticsSerializer(serializers.Serializer):
    """Serializer pour les statistiques FeexPay."""
    
    total_transactions = serializers.IntegerField(read_only=True)
    total_volume = serializers.DecimalField(
        max_digits=15,
        decimal_places=2,
        read_only=True
    )
    success_rate = serializers.DecimalField(
        max_digits=5,
        decimal_places=2,
        read_only=True
    )
    pending_transactions = serializers.IntegerField(read_only=True)
    failed_transactions = serializers.IntegerField(read_only=True)
    average_processing_time = serializers.IntegerField(read_only=True)


class FeexPayErrorResponseSerializer(serializers.Serializer):
    """Serializer pour les réponses d'erreur."""
    
    error_code = serializers.CharField()
    error_message = serializers.CharField()
    details = serializers.JSONField(required=False)
    timestamp = serializers.DateTimeField()
