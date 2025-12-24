# apps/payments/models.py
# =========================

import uuid
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.exceptions import ValidationError


class PaymentMethod(models.Model):
    """Méthodes de paiement disponibles."""
    
    METHOD_TYPES = [
        ('mobile_money', _('Mobile Money')),
        ('card', _('Carte bancaire')),
        ('crypto', _('Cryptomonnaie')),
        ('bank_transfer', _('Virement bancaire')),
        ('paypal', _('PayPal')),
        ('stripe', _('Stripe')),
    ]
    
    SUPPORTED_CURRENCIES = [
        ('FCFA', 'FCFA'),
        ('EUR', 'EUR'),
        ('USD', 'USD'),
        ('BTC', 'Bitcoin'),
        ('ETH', 'Ethereum'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('Nom'), max_length=100)
    method_type = models.CharField(_('Type de méthode'), max_length=20, choices=METHOD_TYPES)
    
    # Configuration
    is_active = models.BooleanField(_('Actif'), default=True)
    supported_currencies = models.JSONField(_('Devises supportées'), default=list)
    
    # Limites
    min_deposit = models.JSONField(_('Dépôt minimum par devise'), default=dict)
    max_deposit = models.JSONField(_('Dépôt maximum par devise'), default=dict)
    min_withdrawal = models.JSONField(_('Retrait minimum par devise'), default=dict)
    max_withdrawal = models.JSONField(_('Retrait maximum par devise'), default=dict)
    
    # Frais
    deposit_fee_percentage = models.DecimalField(
        _('Frais de dépôt (%)'),
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00')
    )
    withdrawal_fee_percentage = models.DecimalField(
        _('Frais de retrait (%)'),
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00')
    )
    deposit_fee_fixed = models.DecimalField(
        _('Frais fixes de dépôt'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    withdrawal_fee_fixed = models.DecimalField(
        _('Frais fixes de retrait'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    # Délais de traitement
    deposit_processing_time = models.CharField(
        _('Délai de traitement des dépôts'),
        max_length=50,
        default='Instantané'
    )
    withdrawal_processing_time = models.CharField(
        _('Délai de traitement des retraits'),
        max_length=50,
        default='24-48h'
    )
    
    # Métadonnées
    description = models.TextField(_('Description'), blank=True)
    icon = models.ImageField(_('Icône'), upload_to='payment_icons/', null=True, blank=True)
    
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        db_table = 'payment_methods'
        verbose_name = _('Méthode de paiement')
        verbose_name_plural = _('Méthodes de paiement')
        ordering = ['name']
    
    def __str__(self):
        return self.name
    
    def calculate_fees(self, amount, transaction_type='deposit'):
        """Calculer les frais pour un montant donné."""
        if transaction_type == 'deposit':
            percentage_fee = self.deposit_fee_percentage
            fixed_fee = self.deposit_fee_fixed
        else:
            percentage_fee = self.withdrawal_fee_percentage
            fixed_fee = self.withdrawal_fee_fixed
        
        percentage_amount = amount * (percentage_fee / Decimal('100'))
        total_fees = percentage_amount + fixed_fee
        
        return {
            'percentage_fee': percentage_amount,
            'fixed_fee': fixed_fee,
            'total_fees': total_fees,
            'net_amount': amount - total_fees if transaction_type == 'withdrawal' else amount,
            'gross_amount': amount + total_fees if transaction_type == 'deposit' else amount
        }


class Transaction(models.Model):
    """Transactions financières."""
    
    TRANSACTION_TYPES = [
        ('deposit', _('Dépôt')),
        ('withdrawal', _('Retrait')),
        ('bet', _('Mise')),
        ('win', _('Gain')),
        ('commission', _('Commission')),
        ('referral', _('Commission de parrainage')),
        ('refund', _('Remboursement')),
        ('bonus', _('Bonus')),
        ('penalty', _('Pénalité')),
        ('fee', _('Frais')),
    ]
    
    TRANSACTION_STATUS = [
        ('pending', _('En attente')),
        ('processing', _('En cours de traitement')),
        ('completed', _('Terminé')),
        ('failed', _('Échoué')),
        ('cancelled', _('Annulé')),
        ('expired', _('Expiré')),
        ('disputed', _('En litige')),
        ('refunded', _('Remboursé')),
    ]
    
    CURRENCIES = [
        ('FCFA', 'FCFA'),
        ('EUR', 'EUR'),
        ('USD', 'USD'),
        ('BTC', 'Bitcoin'),
        ('ETH', 'Ethereum'),
    ]
    
    # Identifiants
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    transaction_id = models.CharField(_('ID de transaction'), max_length=100, unique=True, blank=True)
    external_reference = models.CharField(
        _('Référence externe'),
        max_length=100,
        null=True,
        blank=True,
        help_text=_('Référence du processeur de paiement')
    )
    
    # Relations
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name=_('Utilisateur')
    )
    game = models.ForeignKey(
        'games.Game',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name=_('Partie')
    )
    payment_method = models.ForeignKey(
        PaymentMethod,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='transactions',
        verbose_name=_('Méthode de paiement')
    )
    
    # Détails de la transaction
    transaction_type = models.CharField(_('Type'), max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(
        _('Montant'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    currency = models.CharField(_('Devise'), max_length=5, choices=CURRENCIES)
    
    # Frais
    fees = models.DecimalField(
        _('Frais'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    net_amount = models.DecimalField(
        _('Montant net'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    # État
    status = models.CharField(_('Statut'), max_length=20, choices=TRANSACTION_STATUS, default='pending')
    failure_reason = models.TextField(_('Raison de l\'échec'), blank=True)
    
    # Métadonnées
    metadata = models.JSONField(_('Métadonnées'), default=dict, blank=True)
    notes = models.TextField(_('Notes'), blank=True)
    
    # Timing
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    processed_at = models.DateTimeField(_('Traité le'), null=True, blank=True)
    completed_at = models.DateTimeField(_('Complété le'), null=True, blank=True)
    expires_at = models.DateTimeField(_('Expire le'), null=True, blank=True)
    
    # Audit
    ip_address = models.GenericIPAddressField(_('Adresse IP'), null=True, blank=True)
    user_agent = models.TextField(_('User Agent'), blank=True)
    
    class Meta:
        db_table = 'transactions'
        verbose_name = _('Transaction')
        verbose_name_plural = _('Transactions')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['transaction_type', 'status']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['external_reference']),
            models.Index(fields=['transaction_id']),
        ]
    
    def __str__(self):
        return f"{self.get_transaction_type_display()} - {self.amount} {self.currency} ({self.get_status_display()})"
    
    def save(self, *args, **kwargs):
        # Générer un ID de transaction unique
        if not self.transaction_id:
            self.transaction_id = self.generate_transaction_id()
        
        # Calculer le montant net
        if not self.net_amount:
            self.net_amount = self.amount - self.fees
        
        super().save(*args, **kwargs)
    
    def generate_transaction_id(self):
        """Générer un ID de transaction unique."""
        import string
        import secrets
        
        prefix_map = {
            'deposit': 'DEP',
            'withdrawal': 'WDR',
            'bet': 'BET',
            'win': 'WIN',
            'commission': 'COM',
            'referral': 'REF',
            'refund': 'RFD',
            'bonus': 'BON',
            'penalty': 'PEN',
            'fee': 'FEE',
        }
        
        prefix = prefix_map.get(self.transaction_type, 'TXN')
        timestamp = timezone.now().strftime('%Y%m%d')
        random_part = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
        
        return f"{prefix}{timestamp}{random_part}"
    
    def can_cancel(self):
        """Vérifier si la transaction peut être annulée."""
        return self.status in ['pending', 'processing'] and self.transaction_type in ['deposit', 'withdrawal']
    
    def cancel(self, reason='User cancelled'):
        """Annuler la transaction."""
        if not self.can_cancel():
            raise ValidationError(_('Cette transaction ne peut pas être annulée'))
        
        self.status = 'cancelled'
        self.failure_reason = reason
        self.processed_at = timezone.now()
        self.save()
        
        # Si c'était un retrait, rembourser le montant
        if self.transaction_type == 'withdrawal':
            self.user.update_balance(self.currency, self.amount, 'add')
    
    def process(self):
        """Traiter la transaction."""
        if self.status != 'pending':
            raise ValidationError(_('Seules les transactions en attente peuvent être traitées'))
        
        self.status = 'processing'
        self.processed_at = timezone.now()
        self.save()
        
        # Logique de traitement selon le type
        if self.transaction_type == 'deposit':
            self._process_deposit()
        elif self.transaction_type == 'withdrawal':
            self._process_withdrawal()
        elif self.transaction_type in ['bet', 'win', 'commission', 'referral']:
            self._process_internal_transaction()
    
    def _process_deposit(self):
        """Traiter un dépôt."""
        try:
            # Créditer le compte utilisateur
            self.user.update_balance(self.currency, self.net_amount, 'add')
            
            self.status = 'completed'
            self.completed_at = timezone.now()
            self.save()
            
            # Envoyer notification
            self._send_transaction_notification('deposit_completed')
            
        except Exception as e:
            self.status = 'failed'
            self.failure_reason = str(e)
            self.save()
            raise
    
    def _process_withdrawal(self):
        """Traiter un retrait."""
        try:
            # Vérifier les fonds suffisants
            if self.user.get_balance(self.currency) < self.amount:
                raise ValidationError(_('Fonds insuffisants'))
            
            # Débiter le compte utilisateur
            self.user.update_balance(self.currency, self.amount, 'subtract')
            
            # Dans un vrai système, on appellerait l'API du processeur de paiement ici
            self.status = 'completed'
            self.completed_at = timezone.now()
            self.save()
            
            # Envoyer notification
            self._send_transaction_notification('withdrawal_completed')
            
        except Exception as e:
            self.status = 'failed'
            self.failure_reason = str(e)
            self.save()
            raise
    
    def _process_internal_transaction(self):
        """Traiter une transaction interne (mise, gain, etc.)."""
        try:
            if self.transaction_type == 'bet':
                # Débiter pour une mise
                self.user.update_balance(self.currency, self.amount, 'subtract')
            elif self.transaction_type in ['win', 'commission', 'referral', 'bonus']:
                # Créditer pour un gain
                self.user.update_balance(self.currency, self.amount, 'add')
            
            self.status = 'completed'
            self.completed_at = timezone.now()
            self.save()
            
        except Exception as e:
            self.status = 'failed'
            self.failure_reason = str(e)
            self.save()
            raise
    
    def _send_transaction_notification(self, notification_type):
        """Envoyer une notification de transaction."""
        from django.core.mail import send_mail
        from django.template.loader import render_to_string
        
        subject_map = {
            'deposit_completed': _('Dépôt confirmé'),
            'withdrawal_completed': _('Retrait traité'),
            'transaction_failed': _('Transaction échouée'),
        }
        
        subject = subject_map.get(notification_type, _('Notification de transaction'))
        
        # Ici on enverrait l'email de notification
        # send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [self.user.email])


class Wallet(models.Model):
    """Portefeuille utilisateur pour chaque devise."""
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wallets',
        verbose_name=_('Utilisateur')
    )
    currency = models.CharField(_('Devise'), max_length=5, choices=Transaction.CURRENCIES)
    
    # Soldes
    available_balance = models.DecimalField(
        _('Solde disponible'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    locked_balance = models.DecimalField(
        _('Solde bloqué'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        validators=[MinValueValidator(Decimal('0.00'))]
    )
    total_deposited = models.DecimalField(
        _('Total déposé'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    total_withdrawn = models.DecimalField(
        _('Total retiré'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    last_transaction_at = models.DateTimeField(_('Dernière transaction'), null=True, blank=True)
    
    class Meta:
        db_table = 'wallets'
        verbose_name = _('Portefeuille')
        verbose_name_plural = _('Portefeuilles')
        unique_together = ['user', 'currency']
        indexes = [
            models.Index(fields=['user', 'currency']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.currency}"
    
    @property
    def total_balance(self):
        """Solde total (disponible + bloqué)."""
        return self.available_balance + self.locked_balance
    
    def lock_funds(self, amount):
        """Bloquer des fonds."""
        if self.available_balance < amount:
            raise ValidationError(_('Fonds insuffisants pour bloquer'))
        
        self.available_balance -= amount
        self.locked_balance += amount
        self.save()
    
    def unlock_funds(self, amount):
        """Débloquer des fonds."""
        if self.locked_balance < amount:
            raise ValidationError(_('Pas assez de fonds bloqués'))
        
        self.locked_balance -= amount
        self.available_balance += amount
        self.save()
    
    def transfer_locked_funds(self, amount, to_available=True):
        """Transférer des fonds bloqués."""
        if self.locked_balance < amount:
            raise ValidationError(_('Pas assez de fonds bloqués'))
        
        self.locked_balance -= amount
        if to_available:
            self.available_balance += amount
        
        self.save()


class WithdrawalRequest(models.Model):
    """Demandes de retrait."""
    
    STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('approved', _('Approuvé')),
        ('rejected', _('Rejeté')),
        ('processing', _('En cours de traitement')),
        ('completed', _('Terminé')),
        ('failed', _('Échoué')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='withdrawal_requests',
        verbose_name=_('Utilisateur')
    )
    transaction = models.OneToOneField(
        Transaction,
        on_delete=models.CASCADE,
        related_name='withdrawal_request',
        verbose_name=_('Transaction')
    )
    
    # Détails de la demande
    amount = models.DecimalField(_('Montant'), max_digits=12, decimal_places=2)
    currency = models.CharField(_('Devise'), max_length=5, choices=Transaction.CURRENCIES)
    payment_method = models.ForeignKey(
        PaymentMethod,
        on_delete=models.CASCADE,
        verbose_name=_('Méthode de paiement')
    )
    
    # Détails du bénéficiaire
    recipient_details = models.JSONField(_('Détails du bénéficiaire'))
    
    # État de la demande
    status = models.CharField(_('Statut'), max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(_('Notes admin'), blank=True)
    rejection_reason = models.TextField(_('Raison du rejet'), blank=True)
    
    # Processus d'approbation
    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='reviewed_withwithdrawals',
        verbose_name=_('Révisé par')
    )
    reviewed_at = models.DateTimeField(_('Révisé le'), null=True, blank=True)
    
    # Timing
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    processed_at = models.DateTimeField(_('Traité le'), null=True, blank=True)
    
    class Meta:
        db_table = 'withdrawal_requests'
        verbose_name = _('Demande de retrait')
        verbose_name_plural = _('Demandes de retrait')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Retrait {self.amount} {self.currency} - {self.user.username}"
    
    def approve(self, admin_user, notes=''):
        """Approuver la demande de retrait."""
        if self.status != 'pending':
            raise ValidationError(_('Seules les demandes en attente peuvent être approuvées'))
        
        self.status = 'approved'
        self.reviewed_by = admin_user
        self.reviewed_at = timezone.now()
        self.admin_notes = notes
        self.save()
        
        # Traiter la transaction
        self.transaction.process()
    
    def reject(self, admin_user, reason):
        """Rejeter la demande de retrait."""
        if self.status != 'pending':
            raise ValidationError(_('Seules les demandes en attente peuvent être rejetées'))
        
        self.status = 'rejected'
        self.reviewed_by = admin_user
        self.reviewed_at = timezone.now()
        self.rejection_reason = reason
        self.save()
        
        # Annuler la transaction et rembourser
        self.transaction.cancel(reason)


class PaymentWebhook(models.Model):
    """Webhooks reçus des processeurs de paiement."""


class FeexPayWithdrawal(models.Model):
    """
    Modèle pour les retraits FeexPay (transferts sortants)
    Simplifié et optimisé pour les transferts Mobile Money
    """
    
    NETWORK_CHOICES = [
        ('MTN', 'MTN Mobile Money'),
        ('ORANGE', 'Orange Money'),
        ('MOOV', 'Moov Money'),
        ('WAVE', 'Wave'),
        ('CELTIIS', 'Celtiis'),
        ('TOGOCOM', 'Togocom'),
        ('FREE', 'Free Money'),
    ]
    
    STATUS_CHOICES = [
        ('pending', 'En attente'),
        ('processing', 'En cours'),
        ('completed', 'Terminé'),
        ('failed', 'Échoué'),
        ('cancelled', 'Annulé'),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='feexpay_withdrawals',
        verbose_name='Utilisateur',
        help_text='Utilisateur demandeur'
    )
    
    # Détails du retrait
    amount = models.DecimalField(
        'Montant',
        max_digits=12,
        decimal_places=2,
        help_text='Montant en FCFA'
    )
    fee = models.DecimalField(
        'Frais',
        max_digits=12,
        decimal_places=2,
        default=0,
        help_text='Frais de retrait'
    )
    
    # Destinataire
    phone_number = models.CharField(
        'Numéro de téléphone',
        max_length=20,
        help_text='Numéro Mobile Money destinataire'
    )
    network = models.CharField(
        'Réseau',
        max_length=20,
        choices=NETWORK_CHOICES,
        help_text='Réseau Mobile Money'
    )
    recipient_name = models.CharField(
        'Nom du bénéficiaire',
        max_length=100,
        help_text='Nom du bénéficiaire'
    )
    description = models.CharField(
        'Description',
        max_length=200,
        blank=True,
        help_text='Description du retrait'
    )
    
    # Statut et traitement
    status = models.CharField(
        'Statut',
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )
    
    # FeexPay
    feexpay_transfer_id = models.CharField(
        'ID FeexPay',
        max_length=100,
        blank=True,
        null=True,
        help_text='ID de transfert FeexPay'
    )
    feexpay_response = models.JSONField(
        'Réponse FeexPay',
        default=dict,
        blank=True,
        help_text='Réponse complète de FeexPay'
    )
    error_message = models.TextField(
        'Message d\'erreur',
        blank=True,
        help_text='Message d\'erreur en cas d\'échec'
    )
    
    # Timestamps
    created_at = models.DateTimeField('Créé le', auto_now_add=True)
    updated_at = models.DateTimeField('Mis à jour le', auto_now=True)
    processed_at = models.DateTimeField(
        'Traité le',
        null=True,
        blank=True,
        help_text='Date de traitement'
    )
    
    class Meta:
        db_table = 'feexpay_withdrawals'
        verbose_name = 'Retrait FeexPay'
        verbose_name_plural = 'Retraits FeexPay'
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Retrait {self.amount} FCFA vers {self.phone_number} ({self.network}) - {self.status}"
    
    @property
    def total_deduction(self):
        """Montant total déduit du compte (montant + frais)"""
        return self.amount + self.fee
    
    @property
    def is_successful(self):
        """Retour True si le retrait est réussi"""
        return self.status == 'completed'
    
    @property
    def is_pending(self):
        """Retour True si le retrait est en attente"""
        return self.status in ['pending', 'processing']
    
    def mark_as_completed(self, transfer_id=None, response_data=None):
        """Marquer le retrait comme terminé"""
        self.status = 'completed'
        self.processed_at = timezone.now()
        if transfer_id:
            self.feexpay_transfer_id = transfer_id
        if response_data:
            self.feexpay_response = response_data
        self.save()
    
    def mark_as_failed(self, error_message, response_data=None):
        """Marquer le retrait comme échoué"""
        self.status = 'failed'
        self.error_message = error_message
        self.processed_at = timezone.now()
        if response_data:
            self.feexpay_response = response_data
        self.save()
    
    def cancel(self, reason=''):
        """Annuler le retrait"""
        self.status = 'cancelled'
        if reason:
            self.error_message = reason
        self.processed_at = timezone.now()
        self.save()


class PaymentWebhook(models.Model):
    """Webhooks reçus des processeurs de paiement."""
    
    STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('processed', _('Traité')),
        ('failed', _('Échoué')),
        ('ignored', _('Ignoré')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Source du webhook
    provider = models.CharField(_('Fournisseur'), max_length=50)
    webhook_id = models.CharField(_('ID du webhook'), max_length=255, blank=True)
    event_type = models.CharField(_('Type d\'événement'), max_length=100)
    
    # Données
    payload = models.JSONField(_('Données'))
    headers = models.JSONField(_('En-têtes HTTP'), default=dict)
    
    # Traitement
    status = models.CharField(_('Statut'), max_length=20, choices=STATUS_CHOICES, default='pending')
    processed_at = models.DateTimeField(_('Traité le'), null=True, blank=True)
    error_message = models.TextField(_('Message d\'erreur'), blank=True)
    
    # Relations
    transaction = models.ForeignKey(
        Transaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='webhooks',
        verbose_name=_('Transaction')
    )
    
    # Métadonnées
    ip_address = models.GenericIPAddressField(_('Adresse IP'), null=True, blank=True)
    user_agent = models.TextField(_('User Agent'), blank=True)
    created_at = models.DateTimeField(_('Reçu le'), auto_now_add=True)
    
    class Meta:
        db_table = 'payment_webhooks'
        verbose_name = _('Webhook de paiement')
        verbose_name_plural = _('Webhooks de paiement')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['provider', 'event_type']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['webhook_id']),
        ]
    
    def __str__(self):
        return f"{self.provider} - {self.event_type} ({self.get_status_display()})"
    
    def process_webhook(self):
        """Traiter le webhook."""
        if self.status != 'pending':
            return
        
        try:
            # Logique de traitement selon le fournisseur
            processor_map = {
                'stripe': self._process_stripe_webhook,
                'mobile_money': self._process_mobile_money_webhook,
                'crypto': self._process_crypto_webhook,
            }
            
            processor = processor_map.get(self.provider)
            if processor:
                processor()
                self.status = 'processed'
                self.processed_at = timezone.now()
            else:
                self.status = 'ignored'
                self.error_message = f'Fournisseur non supporté: {self.provider}'
            
        except Exception as e:
            self.status = 'failed'
            self.error_message = str(e)
        
        self.save()
    
    def _process_stripe_webhook(self):
        """Traiter un webhook Stripe."""
        event_type = self.event_type
        event_data = self.payload.get('data', {}).get('object', {})
        
        if event_type == 'payment_intent.succeeded':
            # Traitement d'un paiement réussi
            payment_intent_id = event_data.get('id')
            transaction = Transaction.objects.filter(
                external_reference=payment_intent_id,
                status='processing'
            ).first()
            
            if transaction:
                transaction.status = 'completed'
                transaction.completed_at = timezone.now()
                transaction.save()
                self.transaction = transaction
        
        elif event_type == 'payment_intent.payment_failed':
            # Traitement d'un paiement échoué
            payment_intent_id = event_data.get('id')
            transaction = Transaction.objects.filter(
                external_reference=payment_intent_id,
                status='processing'
            ).first()
            
            if transaction:
                transaction.status = 'failed'
                transaction.failure_reason = 'Payment failed on Stripe'
                transaction.save()
                self.transaction = transaction
    
    def _process_mobile_money_webhook(self):
        """Traiter un webhook Mobile Money."""
        # Logique spécifique au Mobile Money
        pass
    
    def _process_crypto_webhook(self):
        """Traiter un webhook de crypto."""
        # Logique spécifique aux cryptomonnaies
        pass


class ExchangeRate(models.Model):
    """Taux de change entre devises."""
    
    from_currency = models.CharField(_('Devise source'), max_length=5)
    to_currency = models.CharField(_('Devise cible'), max_length=5)
    rate = models.DecimalField(_('Taux'), max_digits=15, decimal_places=8)
    
    # Métadonnées
    source = models.CharField(_('Source'), max_length=50, default='manual')
    is_active = models.BooleanField(_('Actif'), default=True)
    
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        db_table = 'exchange_rates'
        verbose_name = _('Taux de change')
        verbose_name_plural = _('Taux de change')
        unique_together = ['from_currency', 'to_currency']
        indexes = [
            models.Index(fields=['from_currency', 'to_currency']),
            models.Index(fields=['updated_at']),
        ]
    
    def __str__(self):
        return f"{self.from_currency} → {self.to_currency}: {self.rate}"
    
    @classmethod
    def convert_amount(cls, amount, from_currency, to_currency):
        """Convertir un montant d'une devise à une autre."""
        if from_currency == to_currency:
            return amount
        
        try:
            rate_obj = cls.objects.get(
                from_currency=from_currency,
                to_currency=to_currency,
                is_active=True
            )
            return amount * rate_obj.rate
        except cls.DoesNotExist:
            # Essayer la conversion inverse
            try:
                rate_obj = cls.objects.get(
                    from_currency=to_currency,
                    to_currency=from_currency,
                    is_active=True
                )
                return amount / rate_obj.rate
            except cls.DoesNotExist:
                raise ValidationError(
                    f'Taux de change non disponible: {from_currency} → {to_currency}'
                )


class PaymentSettings(models.Model):
    """Paramètres globaux de paiement."""
    
    # Limites globales
    daily_withdrawal_limit = models.DecimalField(
        _('Limite de retrait quotidien'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('100000.00')
    )
    monthly_withdrawal_limit = models.DecimalField(
        _('Limite de retrait mensuel'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('1000000.00')
    )
    
    # Règles de dépôt
    deposit_usage_requirement = models.DecimalField(
        _('Utilisation obligatoire des dépôts (%)'),
        max_digits=5,
        decimal_places=2,
        default=Decimal('60.00'),
        help_text=_('Pourcentage du dépôt qui doit être misé avant retrait')
    )
    
    # Paramètres KYC
    kyc_required_amount = models.DecimalField(
        _('Montant nécessitant KYC'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('10000.00')
    )
    
    # Configuration
    auto_approval_limit = models.DecimalField(
        _('Limite d\'approbation automatique'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('5000.00')
    )
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        db_table = 'payment_settings'
        verbose_name = _('Paramètres de paiement')
        verbose_name_plural = _('Paramètres de paiement')
    
    def __str__(self):
        return "Paramètres de paiement"
    
    @classmethod
    def get_settings(cls):
        """Obtenir les paramètres de paiement (singleton)."""
        settings, created = cls.objects.get_or_create(pk=1)
        return settings


class FeexPayProvider(models.Model):
    """Fournisseur FeexPay avec configuration des 16 méthodes de paiement."""
    
    PROVIDERS = [
        ('mtn', _('MTN')),
        ('moov', _('Moov')),
        ('orange', _('Orange')),
        ('celtiis', _('Celtiis')),
        ('coris', _('Coris Bank')),
        ('wave', _('Wave')),
        ('free', _('Free')),
        ('bank_transfer', _('Virement Bancaire')),
        ('mastercard', _('Mastercard')),
        ('visa', _('Visa')),
        ('amex', _('American Express')),
        ('unionpay', _('UnionPay')),
        ('orange_ci', _('Orange Côte d\'Ivoire')),
        ('moov_togo', _('Moov Togo')),
        ('mtn_senegal', _('MTN Sénégal')),
        ('wave_senegal', _('Wave Sénégal')),
    ]
    
    COUNTRY_CODES = [
        ('SN', _('Sénégal')),
        ('CI', _('Côte d\'Ivoire')),
        ('TG', _('Togo')),
        ('BJ', _('Bénin')),
        ('GW', _('Guinée-Bissau')),
        ('CM', _('Cameroun')),
        ('GA', _('Gabon')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    provider_code = models.CharField(
        _('Code du fournisseur'),
        max_length=30,
        unique=True,
        choices=PROVIDERS
    )
    provider_name = models.CharField(_('Nom du fournisseur'), max_length=100)
    country_code = models.CharField(_('Code pays'), max_length=2, choices=COUNTRY_CODES)
    
    # Configuration FeexPay
    is_active = models.BooleanField(_('Actif'), default=True)
    is_test_mode = models.BooleanField(_('Mode test'), default=False)
    
    # Limites de transaction
    min_amount = models.DecimalField(
        _('Montant minimum'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('100.00')
    )
    max_amount = models.DecimalField(
        _('Montant maximum'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('1000000.00')
    )
    
    # Frais
    fee_percentage = models.DecimalField(
        _('Frais (%)'),
        max_digits=5,
        decimal_places=2,
        default=Decimal('0.00')
    )
    fee_fixed = models.DecimalField(
        _('Frais fixes'),
        max_digits=8,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    # Devises supportées
    supported_currencies = models.JSONField(
        _('Devises supportées'),
        default=list,
        help_text=_('Ex: ["XOF", "EUR", "USD"]')
    )
    
    # Délais de traitement
    processing_time_seconds = models.IntegerField(
        _('Délai de traitement (secondes)'),
        default=300,
        help_text=_('Délai estimé pour traiter une transaction')
    )
    
    # Métadonnées
    description = models.TextField(_('Description'), blank=True)
    icon_url = models.URLField(_('URL de l\'icône'), blank=True)
    
    # Statistiques
    total_transactions = models.BigIntegerField(_('Total de transactions'), default=0)
    total_volume = models.DecimalField(
        _('Volume total'),
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00')
    )
    success_rate = models.DecimalField(
        _('Taux de réussite (%)'),
        max_digits=5,
        decimal_places=2,
        default=Decimal('100.00')
    )
    
    # Audit
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    last_sync_at = models.DateTimeField(_('Dernière synchronisation'), null=True, blank=True)
    
    class Meta:
        db_table = 'feexpay_providers'
        verbose_name = _('Fournisseur FeexPay')
        verbose_name_plural = _('Fournisseurs FeexPay')
        unique_together = ['provider_code', 'country_code']
        ordering = ['provider_name', 'country_code']
    
    def __str__(self):
        return f"{self.get_provider_code_display()} - {self.get_country_code_display()}"
    
    def calculate_fees(self, amount):
        """Calculer les frais pour un montant donné."""
        percentage_amount = amount * (self.fee_percentage / Decimal('100'))
        total_fees = percentage_amount + self.fee_fixed
        return {
            'percentage_fee': percentage_amount,
            'fixed_fee': self.fee_fixed,
            'total_fees': total_fees,
            'net_amount': amount + total_fees,
        }
    
    def validate_amount(self, amount):
        """Valider si le montant est dans les limites."""
        if amount < self.min_amount:
            raise ValidationError(
                f'Montant minimum: {self.min_amount} {self.supported_currencies[0]}'
            )
        if amount > self.max_amount:
            raise ValidationError(
                f'Montant maximum: {self.max_amount} {self.supported_currencies[0]}'
            )
        return True


class FeexPayTransaction(models.Model):
    """Transaction FeexPay avec suivi complet de l'état."""
    
    PAYMENT_STATUS = [
        ('pending', _('En attente')),
        ('processing', _('En cours de traitement')),
        ('pending_validation', _('En attente de validation')),
        ('successful', _('Réussi')),
        ('failed', _('Échoué')),
        ('cancelled', _('Annulé')),
        ('expired', _('Expiré')),
        ('disputed', _('En litige')),
    ]
    
    PAYMENT_METHODS = [
        ('mobile_money', _('Mobile Money')),
        ('bank_transfer', _('Virement Bancaire')),
        ('card', _('Carte Bancaire')),
        ('wallet', _('Portefeuille Numérique')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Identifiants
    feexpay_transaction_id = models.CharField(
        _('ID de transaction FeexPay'),
        max_length=255,
        unique=True,
        blank=True
    )
    internal_transaction_id = models.CharField(
        _('ID de transaction interne'),
        max_length=255,
        unique=True
    )
    
    # Relations
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='feexpay_transactions',
        verbose_name=_('Utilisateur')
    )
    transaction = models.OneToOneField(
        Transaction,
        on_delete=models.CASCADE,
        related_name='feexpay_transaction',
        verbose_name=_('Transaction')
    )
    provider = models.ForeignKey(
        FeexPayProvider,
        on_delete=models.CASCADE,
        related_name='transactions',
        verbose_name=_('Fournisseur')
    )
    
    # Détails de paiement
    amount = models.DecimalField(
        _('Montant'),
        max_digits=12,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    currency = models.CharField(_('Devise'), max_length=5)
    payment_method = models.CharField(
        _('Méthode de paiement'),
        max_length=50,
        choices=PAYMENT_METHODS
    )
    
    # Destinataire
    recipient_phone = models.CharField(
        _('Numéro de téléphone du destinataire'),
        max_length=20,
        blank=True
    )
    recipient_email = models.EmailField(_('Email du destinataire'), blank=True)
    recipient_account = models.CharField(
        _('Compte du destinataire'),
        max_length=255,
        blank=True,
        help_text=_('Numéro de compte bancaire ou identifiant du portefeuille')
    )
    
    # État
    status = models.CharField(
        _('Statut'),
        max_length=20,
        choices=PAYMENT_STATUS,
        default='pending'
    )
    status_message = models.TextField(_('Message de statut'), blank=True)
    
    # Frais et montants
    fee_amount = models.DecimalField(
        _('Montant des frais'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    gross_amount = models.DecimalField(
        _('Montant brut (montant + frais)'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    # Métadonnées FeexPay
    payment_reference = models.CharField(
        _('Référence de paiement'),
        max_length=255,
        blank=True
    )
    callback_status = models.CharField(
        _('Statut du callback'),
        max_length=50,
        blank=True
    )
    
    # Réponse API
    feexpay_response = models.JSONField(
        _('Réponse FeexPay'),
        default=dict,
        blank=True
    )
    error_code = models.CharField(
        _('Code d\'erreur'),
        max_length=100,
        blank=True
    )
    error_message = models.TextField(_('Message d\'erreur'), blank=True)
    
    # Timing
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    initiated_at = models.DateTimeField(_('Initié le'), null=True, blank=True)
    processed_at = models.DateTimeField(_('Traité le'), null=True, blank=True)
    completed_at = models.DateTimeField(_('Complété le'), null=True, blank=True)
    expires_at = models.DateTimeField(_('Expire le'), null=True, blank=True)
    
    # Audit
    ip_address = models.GenericIPAddressField(_('Adresse IP'), null=True, blank=True)
    user_agent = models.TextField(_('User Agent'), blank=True)
    retry_count = models.IntegerField(_('Nombre de tentatives'), default=0)
    last_retry_at = models.DateTimeField(_('Dernière tentative'), null=True, blank=True)
    
    # Notes
    notes = models.TextField(_('Notes internes'), blank=True)
    
    class Meta:
        db_table = 'feexpay_transactions'
        verbose_name = _('Transaction FeexPay')
        verbose_name_plural = _('Transactions FeexPay')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['feexpay_transaction_id']),
            models.Index(fields=['internal_transaction_id']),
            models.Index(fields=['provider', 'status']),
        ]
    
    def __str__(self):
        return f"FeexPay - {self.amount} {self.currency} ({self.get_status_display()})"
    
    def can_retry(self):
        """Vérifier si la transaction peut être réessayée."""
        if self.retry_count >= 3:
            return False
        if self.status not in ['failed', 'pending']:
            return False
        return True
    
    def mark_as_processing(self):
        """Marquer la transaction comme en cours de traitement."""
        self.status = 'processing'
        self.initiated_at = timezone.now()
        
        # Calculer l'heure d'expiration
        if self.provider.processing_time_seconds:
            self.expires_at = timezone.now() + timezone.timedelta(
                seconds=self.provider.processing_time_seconds * 2
            )
        
        self.save()
    
    def mark_as_successful(self, feexpay_tx_id=None, callback_status=None):
        """Marquer la transaction comme réussie."""
        self.status = 'successful'
        self.completed_at = timezone.now()
        if feexpay_tx_id:
            self.feexpay_transaction_id = feexpay_tx_id
        if callback_status:
            self.callback_status = callback_status
        self.save()
        
        # Mettre à jour la transaction principale
        self.transaction.status = 'completed'
        self.transaction.completed_at = timezone.now()
        self.transaction.external_reference = feexpay_tx_id
        self.transaction.save()
    
    def mark_as_failed(self, error_code, error_message):
        """Marquer la transaction comme échouée."""
        self.status = 'failed'
        self.processed_at = timezone.now()
        self.error_code = error_code
        self.error_message = error_message
        self.save()
        
        # Mettre à jour la transaction principale
        self.transaction.status = 'failed'
        self.transaction.failure_reason = error_message
        self.transaction.save()
    
    def retry(self):
        """Relancer la transaction."""
        if not self.can_retry():
            raise ValidationError(_('Cette transaction ne peut pas être relancée'))
        
        self.retry_count += 1
        self.last_retry_at = timezone.now()
        self.status = 'pending'
        self.save()


class FeexPayWebhookSignature(models.Model):
    """Signature des webhooks FeexPay pour validation de sécurité."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Identifiants
    webhook_id = models.CharField(
        _('ID du webhook'),
        max_length=255,
        unique=True
    )
    event_type = models.CharField(_('Type d\'événement'), max_length=100)
    
    # Données du webhook
    payload = models.JSONField(_('Données du webhook'))
    signature = models.CharField(
        _('Signature HMAC'),
        max_length=255,
        help_text=_('SHA256 de la charge utile signée avec la clé secrète FeexPay')
    )
    headers = models.JSONField(_('En-têtes HTTP'), default=dict)
    
    # Validation
    is_valid = models.BooleanField(_('Signature valide'), default=False)
    validation_error = models.TextField(_('Erreur de validation'), blank=True)
    
    # Transaction associée
    transaction = models.ForeignKey(
        FeexPayTransaction,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='webhook_signatures',
        verbose_name=_('Transaction')
    )
    
    # Traitement
    is_processed = models.BooleanField(_('Traité'), default=False)
    processed_at = models.DateTimeField(_('Traité le'), null=True, blank=True)
    processing_error = models.TextField(_('Erreur de traitement'), blank=True)
    
    # Métadonnées
    ip_address = models.GenericIPAddressField(_('Adresse IP source'), null=True, blank=True)
    user_agent = models.TextField(_('User Agent'), blank=True)
    received_at = models.DateTimeField(_('Reçu le'), auto_now_add=True)
    
    # Retry
    retry_count = models.IntegerField(_('Nombre de tentatives'), default=0)
    next_retry_at = models.DateTimeField(_('Prochaine tentative'), null=True, blank=True)
    
    class Meta:
        db_table = 'feexpay_webhook_signatures'
        verbose_name = _('Signature du webhook FeexPay')
        verbose_name_plural = _('Signatures des webhooks FeexPay')
        ordering = ['-received_at']
        indexes = [
            models.Index(fields=['webhook_id']),
            models.Index(fields=['is_valid', 'is_processed']),
            models.Index(fields=['event_type']),
            models.Index(fields=['received_at']),
        ]
    
    def __str__(self):
        return f"Webhook {self.webhook_id} - {self.event_type}"
    
    def can_retry(self):
        """Vérifier si le webhook peut être retraité."""
        if self.retry_count >= 5:
            return False
        if self.is_processed and not self.processing_error:
            return False
        return True
    
    def mark_as_valid(self):
        """Marquer la signature comme valide."""
        self.is_valid = True
        self.save()
    
    def mark_as_invalid(self, error):
        """Marquer la signature comme invalide."""
        self.is_valid = False
        self.validation_error = error
        self.save()
    
    def mark_as_processed(self):
        """Marquer le webhook comme traité."""
        self.is_processed = True
        self.processed_at = timezone.now()
        self.save()
    
    def mark_as_processing_error(self, error):
        """Enregistrer une erreur de traitement."""
        self.processing_error = error
        self.retry_count += 1
        if self.retry_count < 5:
            self.next_retry_at = timezone.now() + timezone.timedelta(
                seconds=60 * (2 ** self.retry_count)  # Backoff exponentiel
            )
        self.save()
