# apps/payments/serializers.py
# ==============================

from decimal import Decimal
from rest_framework import serializers
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import models

from .models import (
    PaymentMethod, Transaction, Wallet, WithdrawalRequest,
    PaymentWebhook, ExchangeRate, PaymentSettings
)
from apps.accounts.models import User


class PaymentMethodSerializer(serializers.ModelSerializer):
    """Serializer pour les méthodes de paiement."""
    
    fees_info = serializers.SerializerMethodField()
    is_available = serializers.SerializerMethodField()
    
    class Meta:
        model = PaymentMethod
        fields = [
            'id', 'name', 'method_type', 'is_active', 'supported_currencies',
            'min_deposit', 'max_deposit', 'min_withdrawal', 'max_withdrawal',
            'deposit_processing_time', 'withdrawal_processing_time',
            'description', 'icon', 'fees_info', 'is_available'
        ]
        read_only_fields = ['id', 'fees_info', 'is_available']
    
    def get_fees_info(self, obj):
        """Obtenir les informations sur les frais."""
        return {
            'deposit': {
                'percentage': float(obj.deposit_fee_percentage),
                'fixed': float(obj.deposit_fee_fixed)
            },
            'withdrawal': {
                'percentage': float(obj.withdrawal_fee_percentage),
                'fixed': float(obj.withdrawal_fee_fixed)
            }
        }
    
    def get_is_available(self, obj):
        """Vérifier si la méthode est disponible pour l'utilisateur."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return obj.is_active
        
        # Logique supplémentaire selon l'utilisateur
        user = request.user
        
        # Vérifier KYC pour certaines méthodes
        if obj.method_type in ['card', 'bank_transfer'] and user.kyc_status != 'approved':
            return False
        
        return obj.is_active


class TransactionSerializer(serializers.ModelSerializer):
    """Serializer pour les transactions."""
    
    transaction_type_display = serializers.CharField(
        source='get_transaction_type_display', 
        read_only=True
    )
    status_display = serializers.CharField(
        source='get_status_display', 
        read_only=True
    )
    fees_breakdown = serializers.SerializerMethodField()
    can_cancel = serializers.SerializerMethodField()
    
    class Meta:
        model = Transaction
        fields = [
            'id', 'transaction_id', 'external_reference',
            'transaction_type', 'transaction_type_display',
            'amount', 'currency', 'fees', 'net_amount',
            'status', 'status_display', 'failure_reason',
            'payment_method', 'game', 'metadata',
            'created_at', 'processed_at', 'completed_at',
            'fees_breakdown', 'can_cancel'
        ]
        read_only_fields = [
            'id', 'transaction_id', 'external_reference',
            'transaction_type_display', 'status_display',
            'fees', 'net_amount', 'processed_at', 'completed_at',
            'fees_breakdown', 'can_cancel'
        ]
    
    def get_fees_breakdown(self, obj):
        """Détail des frais appliqués."""
        if obj.payment_method:
            fees_calc = obj.payment_method.calculate_fees(
                obj.amount, 
                obj.transaction_type
            )
            return fees_calc
        return None
    
    def get_can_cancel(self, obj):
        """Vérifier si la transaction peut être annulée."""
        return obj.can_cancel()


class DepositRequestSerializer(serializers.Serializer):
    """Serializer pour les demandes de dépôt."""
    
    amount = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        min_value=Decimal('0.01'),
        help_text=_('Montant à déposer')
    )
    currency = serializers.ChoiceField(
        choices=Transaction.CURRENCIES,
        default='FCFA',
        help_text=_('Devise du dépôt')
    )
    payment_method_id = serializers.UUIDField(
        help_text=_('ID de la méthode de paiement')
    )
    return_url = serializers.URLField(
        required=False,
        help_text=_('URL de retour après paiement')
    )
    phone_number = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=_('Numéro de téléphone (nécessaire pour Mobile Money)')
    )
    metadata = serializers.JSONField(
        required=False,
        default=dict,
        help_text=_('Données supplémentaires')
    )
    
    def validate_amount(self, value):
        """Valider le montant du dépôt."""
        if value <= 0:
            raise serializers.ValidationError(
                _('Le montant doit être positif')
            )
        
        # Vérifier les limites maximales quotidiennes
        user = self.context['request'].user
        today_deposits = Transaction.objects.filter(
            user=user,
            transaction_type='deposit',
            status='completed',
            created_at__date=timezone.now().date()
        ).aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0')
        
        daily_limit = Decimal('100000.00')  # Limite quotidienne par défaut
        if today_deposits + value > daily_limit:
            raise serializers.ValidationError(
                _('Limite quotidienne de dépôt dépassée ({})')
                .format(daily_limit)
            )
        
        return value
    
    def validate_payment_method_id(self, value):
        """Valider la méthode de paiement."""
        try:
            payment_method = PaymentMethod.objects.get(id=value, is_active=True)
        except PaymentMethod.DoesNotExist:
            raise serializers.ValidationError(
                _('Méthode de paiement invalide ou inactive')
            )
        
        # Vérifier si l'utilisateur peut utiliser cette méthode
        user = self.context['request'].user
        if payment_method.method_type in ['card', 'bank_transfer']:
            if user.kyc_status != 'approved':
                raise serializers.ValidationError(
                    _('Vérification KYC requise pour cette méthode')
                )
        
        return value
    
    def validate(self, attrs):
        """Validation croisée."""
        amount = attrs['amount']
        currency = attrs['currency']
        payment_method_id = attrs['payment_method_id']
        
        # Obtenir la méthode de paiement
        payment_method = PaymentMethod.objects.get(id=payment_method_id)
        
        # Vérifier si la devise est supportée
        if currency not in payment_method.supported_currencies:
            raise serializers.ValidationError({
                'currency': _('Cette devise n\'est pas supportée par cette méthode')
            })
        
        # Vérifier les limites min/max
        min_amount = payment_method.min_deposit.get(currency)
        max_amount = payment_method.max_deposit.get(currency)
        
        if min_amount and amount < Decimal(str(min_amount)):
            raise serializers.ValidationError({
                'amount': _('Montant minimum: {} {}').format(min_amount, currency)
            })
        
        if max_amount and amount > Decimal(str(max_amount)):
            raise serializers.ValidationError({
                'amount': _('Montant maximum: {} {}').format(max_amount, currency)
            })

        # Si méthode Mobile Money, un numéro de téléphone est requis
        if payment_method.method_type == 'mobile_money':
            phone = attrs.get('phone_number')
            if not phone:
                raise serializers.ValidationError({
                    'phone_number': _('Numéro de téléphone requis pour Mobile Money')
                })
        
        return attrs


class DepositConfirmSerializer(serializers.Serializer):
    """Serializer pour confirmer un dépôt."""
    
    transaction_id = serializers.UUIDField(
        help_text=_('ID de la transaction à confirmer')
    )
    
    # Champs FeexPay spécifiques
    feexpay_reference = serializers.CharField(
        required=False,
        max_length=255,
        help_text=_('Référence FeexPay de la transaction')
    )
    amount = serializers.DecimalField(
        required=False,
        max_digits=10,
        decimal_places=2,
        help_text=_('Montant confirmé par FeexPay')
    )
    status = serializers.CharField(
        required=False,
        max_length=50,
        help_text=_('Statut de la transaction FeexPay')
    )
    
    # Champs legacy pour compatibilité
    external_reference = serializers.CharField(
        required=False,
        max_length=255,
        help_text=_('Référence externe du paiement (ex: FeexPay transaction ID)')
    )
    payment_proof = serializers.CharField(
        required=False,
        help_text=_('Preuve de paiement ou données de confirmation')
    )
    metadata = serializers.JSONField(
        required=False,
        default=dict,
        help_text=_('Données supplémentaires de confirmation')
    )
    
    def validate_transaction_id(self, value):
        """Valider que la transaction existe et peut être confirmée."""
        try:
            transaction = Transaction.objects.get(id=value)
        except Transaction.DoesNotExist:
            raise serializers.ValidationError(
                _('Transaction introuvable')
            )
        
        # Vérifier que l'utilisateur est propriétaire
        user = self.context['request'].user
        if transaction.user != user:
            raise serializers.ValidationError(
                _('Vous n\'êtes pas autorisé à confirmer cette transaction')
            )
        
        # Vérifier que la transaction peut être confirmée (plus flexible)
        if transaction.status in ['completed', 'failed', 'cancelled']:
            raise serializers.ValidationError(
                _('Cette transaction ne peut plus être confirmée (statut: {})').format(
                    transaction.get_status_display()
                )
            )
        
        # Vérifier que c'est un dépôt
        if transaction.transaction_type != 'deposit':
            raise serializers.ValidationError(
                _('Seuls les dépôts peuvent être confirmés via cette méthode')
            )
        
        return value
    
    def validate(self, attrs):
        """Validation croisée des champs."""
        # Si feexpay_reference est fourni, l'utiliser comme external_reference
        if attrs.get('feexpay_reference') and not attrs.get('external_reference'):
            attrs['external_reference'] = attrs['feexpay_reference']
        
        # Validation du montant FeexPay vs transaction
        if attrs.get('amount'):
            transaction_id = attrs['transaction_id']
            try:
                transaction = Transaction.objects.get(id=transaction_id)
                feexpay_amount = Decimal(str(attrs['amount']))
                
                # Tolérance de 0.01 pour les différences de précision
                if abs(transaction.amount - feexpay_amount) > Decimal('0.01'):
                    # Ajouter un warning dans les métadonnées
                    if not attrs.get('metadata'):
                        attrs['metadata'] = {}
                    attrs['metadata']['amount_mismatch_warning'] = {
                        'django_amount': str(transaction.amount),
                        'feexpay_amount': str(feexpay_amount),
                        'difference': str(transaction.amount - feexpay_amount)
                    }
            except (Transaction.DoesNotExist, ValueError, TypeError):
                pass  # Erreur déjà gérée dans validate_transaction_id
        
        # Validation du statut FeexPay
        valid_statuses = ['completed', 'successful', 'success', 'failed', 'pending', 'processing']
        if attrs.get('status') and attrs['status'].lower() not in valid_statuses:
            raise serializers.ValidationError({
                'status': _('Statut FeexPay invalide. Valeurs acceptées: {}').format(
                    ', '.join(valid_statuses)
                )
            })
        
        return attrs


class WithdrawalRequestSerializer(serializers.ModelSerializer):
    """Serializer pour les demandes de retrait."""
    
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    can_cancel = serializers.SerializerMethodField()
    fees_info = serializers.SerializerMethodField()
    
    class Meta:
        model = WithdrawalRequest
        fields = [
            'id', 'amount', 'currency', 'payment_method',
            'recipient_details', 'status', 'status_display',
            'rejection_reason', 'created_at', 'processed_at',
            'can_cancel', 'fees_info'
        ]
        read_only_fields = [
            'id', 'status', 'status_display', 'rejection_reason',
            'processed_at', 'can_cancel', 'fees_info'
        ]
    
    def get_can_cancel(self, obj):
        """Vérifier si la demande peut être annulée."""
        return obj.status == 'pending'
    
    def get_fees_info(self, obj):
        """Informations sur les frais."""
        if obj.payment_method:
            return obj.payment_method.calculate_fees(
                obj.amount,
                'withdrawal'
            )
        return None
    
    def validate_amount(self, value):
        """Valider le montant du retrait."""
        user = self.context['request'].user
        
        # Vérifier le solde disponible
        user_balance = user.get_balance(self.initial_data.get('currency', 'FCFA'))
        if user_balance < value:
            raise serializers.ValidationError(
                _('Solde insuffisant. Solde disponible: {} {}')
                .format(user_balance, self.initial_data.get('currency', 'FCFA'))
            )
        
        # Vérifier les limites quotidiennes
        today_withdrawals = Transaction.objects.filter(
            user=user,
            transaction_type='withdrawal',
            status='completed',
            created_at__date=timezone.now().date()
        ).aggregate(
            total=models.Sum('amount')
        )['total'] or Decimal('0')
        
        daily_limit = Decimal('50000.00')  # Limite quotidienne par défaut
        if today_withdrawals + value > daily_limit:
            raise serializers.ValidationError(
                _('Limite quotidienne de retrait dépassée ({})')
                .format(daily_limit)
            )
        
        return value
    
    def validate_payment_method(self, value):
        """Valider la méthode de paiement pour retrait."""
        if not value.is_active:
            raise serializers.ValidationError(
                _('Cette méthode de paiement n\'est pas disponible')
            )
        
        user = self.context['request'].user
        
        # Vérifier KYC pour certaines méthodes
        if value.method_type in ['card', 'bank_transfer', 'crypto']:
            if user.kyc_status != 'approved':
                raise serializers.ValidationError(
                    _('Vérification KYC requise pour cette méthode')
                )
        
        return value
    
    def validate_recipient_details(self, value):
        """Valider les détails du bénéficiaire."""
        if not isinstance(value, dict):
            raise serializers.ValidationError(
                _('Les détails du bénéficiaire doivent être un objet')
            )
        
        # Validation selon le type de méthode
        payment_method_id = self.initial_data.get('payment_method')
        if payment_method_id:
            try:
                payment_method = PaymentMethod.objects.get(id=payment_method_id)
                return self._validate_recipient_by_method(value, payment_method)
            except PaymentMethod.DoesNotExist:
                pass
        
        return value
    
    def _validate_recipient_by_method(self, details, payment_method):
        """Valider les détails selon la méthode de paiement."""
        if payment_method.method_type == 'mobile_money':
            required_fields = ['phone_number', 'operator']
            for field in required_fields:
                if field not in details:
                    raise serializers.ValidationError(
                        _('Champ requis pour Mobile Money: {}').format(field)
                    )
        
        elif payment_method.method_type == 'card':
            required_fields = ['card_number', 'card_holder_name']
            for field in required_fields:
                if field not in details:
                    raise serializers.ValidationError(
                        _('Champ requis pour carte: {}').format(field)
                    )
        
        elif payment_method.method_type == 'crypto':
            if 'wallet_address' not in details:
                raise serializers.ValidationError(
                    _('Adresse de portefeuille requise pour crypto')
                )
        
        return details


class WalletSerializer(serializers.ModelSerializer):
    """Serializer pour les portefeuilles."""
    
    total_balance = serializers.DecimalField(
        max_digits=12,
        decimal_places=2,
        read_only=True
    )
    currency_display = serializers.SerializerMethodField()
    
    class Meta:
        model = Wallet
        fields = [
            'currency', 'currency_display', 'available_balance',
            'locked_balance', 'total_balance', 'total_deposited',
            'total_withdrawn', 'last_transaction_at'
        ]
        read_only_fields = [
            'available_balance', 'locked_balance', 'total_balance',
            'total_deposited', 'total_withdrawn', 'last_transaction_at'
        ]
    
    def get_currency_display(self, obj):
        """Nom complet de la devise."""
        currency_names = {
            'FCFA': 'Franc CFA',
            'EUR': 'Euro',
            'USD': 'Dollar US',
            'BTC': 'Bitcoin',
            'ETH': 'Ethereum'
        }
        return currency_names.get(obj.currency, obj.currency)


class ExchangeRateSerializer(serializers.ModelSerializer):
    """Serializer pour les taux de change."""
    
    inverse_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = ExchangeRate
        fields = [
            'from_currency', 'to_currency', 'rate',
            'inverse_rate', 'source', 'updated_at'
        ]
        read_only_fields = ['inverse_rate', 'updated_at']
    
    def get_inverse_rate(self, obj):
        """Taux de change inverse."""
        if obj.rate > 0:
            return 1 / obj.rate
        return 0


class PaymentWebhookSerializer(serializers.ModelSerializer):
    """Serializer pour les webhooks de paiement."""
    
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    
    class Meta:
        model = PaymentWebhook
        fields = [
            'id', 'provider', 'webhook_id', 'event_type',
            'status', 'status_display', 'processed_at',
            'error_message', 'created_at'
        ]
        read_only_fields = '__all__'


class PaymentSettingsSerializer(serializers.ModelSerializer):
    """Serializer pour les paramètres de paiement."""
    
    class Meta:
        model = PaymentSettings
        fields = [
            'daily_withdrawal_limit', 'monthly_withdrawal_limit',
            'deposit_usage_requirement', 'kyc_required_amount',
            'auto_approval_limit'
        ]


class PaymentStatisticsSerializer(serializers.Serializer):
    """Serializer pour les statistiques de paiement utilisateur."""
    
    def to_representation(self, obj):
        """Calculer les statistiques de paiement."""
        from django.db.models import Sum, Count, Q
        
        # Transactions de l'utilisateur
        user_transactions = Transaction.objects.filter(
            user=obj,
            status='completed'
        )
        
        # Dépôts
        deposits = user_transactions.filter(transaction_type='deposit')
        total_deposits = deposits.aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
        deposits_count = deposits.count()
        
        # Retraits
        withdrawals = user_transactions.filter(transaction_type='withdrawal')
        total_withdrawals = withdrawals.aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
        withdrawals_count = withdrawals.count()
        
        # Gains et pertes
        wins = user_transactions.filter(transaction_type='win')
        total_wins = wins.aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
        
        bets = user_transactions.filter(transaction_type='bet')
        total_bets = bets.aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
        
        # Commissions
        commissions = user_transactions.filter(transaction_type='commission')
        total_commissions = commissions.aggregate(Sum('amount'))['amount__sum'] or Decimal('0')
        
        # Calculs
        net_deposits = total_deposits - total_withdrawals
        net_gaming = total_wins - total_bets
        
        return {
            'deposits': {
                'total_amount': total_deposits,
                'count': deposits_count,
                'average': total_deposits / deposits_count if deposits_count > 0 else 0
            },
            'withdrawals': {
                'total_amount': total_withdrawals,
                'count': withdrawals_count,
                'average': total_withdrawals / withdrawals_count if withdrawals_count > 0 else 0
            },
            'gaming': {
                'total_bets': total_bets,
                'total_wins': total_wins,
                'net_result': net_gaming,
                'win_rate': (total_wins / total_bets * 100) if total_bets > 0 else 0
            },
            'commissions': {
                'total_earned': total_commissions,
                'count': commissions.count()
            },
            'summary': {
                'net_deposits': net_deposits,
                'total_transactions': user_transactions.count(),
                'account_value': net_deposits + net_gaming + total_commissions
            },
            'recent_activity': {
                'last_deposit': deposits.order_by('-created_at').first(),
                'last_withdrawal': withdrawals.order_by('-created_at').first(),
                'last_transaction': user_transactions.order_by('-created_at').first()
            }
        }


class FeeCalculatorSerializer(serializers.Serializer):
    """Serializer pour calculer les frais."""
    
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    currency = serializers.ChoiceField(choices=Transaction.CURRENCIES)
    payment_method_id = serializers.UUIDField()
    transaction_type = serializers.ChoiceField(
        choices=['deposit', 'withdrawal'],
        default='deposit'
    )
    
    def validate_payment_method_id(self, value):
        """Valider la méthode de paiement."""
        try:
            return PaymentMethod.objects.get(id=value, is_active=True)
        except PaymentMethod.DoesNotExist:
            raise serializers.ValidationError(
                _('Méthode de paiement invalide')
            )
    
    def get_fee_calculation(self):
        """Obtenir le calcul des frais."""
        validated_data = self.validated_data
        payment_method = validated_data['payment_method_id']
        amount = validated_data['amount']
        transaction_type = validated_data['transaction_type']
        
        return payment_method.calculate_fees(amount, transaction_type)


class CurrencyConversionSerializer(serializers.Serializer):
    """Serializer pour la conversion de devises."""
    
    amount = serializers.DecimalField(max_digits=12, decimal_places=2)
    from_currency = serializers.ChoiceField(choices=Transaction.CURRENCIES)
    to_currency = serializers.ChoiceField(choices=Transaction.CURRENCIES)
    
    def get_conversion(self):
        """Obtenir la conversion."""
        validated_data = self.validated_data
        
        converted_amount = ExchangeRate.convert_amount(
            validated_data['amount'],
            validated_data['from_currency'],
            validated_data['to_currency']
        )
        
        return {
            'original_amount': validated_data['amount'],
            'from_currency': validated_data['from_currency'],
            'to_currency': validated_data['to_currency'],
            'converted_amount': converted_amount,
            'exchange_rate': converted_amount / validated_data['amount'] if validated_data['amount'] > 0 else 0
        }
