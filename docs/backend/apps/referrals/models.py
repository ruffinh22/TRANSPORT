# apps/referrals/models.py
# ==========================

import uuid
import secrets
import string
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.exceptions import ValidationError
from dateutil.relativedelta import relativedelta


class ReferralProgram(models.Model):
    """Programme de parrainage global."""
    
    COMMISSION_TYPES = [
        ('percentage', _('Pourcentage')),
        ('fixed', _('Montant fixe')),
        ('tiered', _('Par paliers')),
    ]
    
    STATUS_CHOICES = [
        ('active', _('Actif')),
        ('inactive', _('Inactif')),
        ('paused', _('En pause')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('Nom du programme'), max_length=200)
    description = models.TextField(_('Description'))
    
    # Configuration des commissions
    commission_type = models.CharField(_('Type de commission'), max_length=20, choices=COMMISSION_TYPES)
    commission_rate = models.DecimalField(
        _('Taux de commission (%)'),
        max_digits=5,
        decimal_places=2,
        default=Decimal('10.00'),
        validators=[MinValueValidator(Decimal('0.01')), MaxValueValidator(Decimal('50.00'))]
    )
    fixed_commission = models.DecimalField(
        _('Commission fixe'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    # Limites
    max_commission_per_referral = models.DecimalField(
        _('Commission max par filleul'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text=_('0 = illimité')
    )
    max_daily_commission = models.DecimalField(
        _('Commission quotidienne max'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text=_('0 = illimité')
    )
    max_monthly_commission = models.DecimalField(
        _('Commission mensuelle max'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text=_('0 = illimité')
    )
    
    # Conditions
    min_bet_for_commission = models.DecimalField(
        _('Mise minimum pour commission'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('100.00')
    )
    free_games_limit = models.PositiveIntegerField(
        _('Limite de parties gratuites'),
        default=3,
        help_text=_('Nombre de parties donnant commission pour utilisateurs non premium')
    )
    
    # État
    status = models.CharField(_('Statut'), max_length=20, choices=STATUS_CHOICES, default='active')
    is_default = models.BooleanField(_('Programme par défaut'), default=False)
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        db_table = 'referral_programs'
        verbose_name = _('Programme de parrainage')
        verbose_name_plural = _('Programmes de parrainage')
        ordering = ['-is_default', 'name']
    
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        # S'assurer qu'un seul programme est par défaut
        if self.is_default:
            ReferralProgram.objects.filter(is_default=True).update(is_default=False)
        super().save(*args, **kwargs)
    
    @classmethod
    def get_default_program(cls):
        """Obtenir le programme de parrainage par défaut."""
        return cls.objects.filter(is_default=True, status='active').first()


class Referral(models.Model):
    """Relation de parrainage entre utilisateurs."""
    
    STATUS_CHOICES = [
        ('active', _('Actif')),
        ('inactive', _('Inactif')),
        ('suspended', _('Suspendu')),
        ('expired', _('Expiré')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relations
    referrer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='referrals_made',
        verbose_name=_('Parrain')
    )
    referred = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='referral_received',
        verbose_name=_('Filleul')
    )
    program = models.ForeignKey(
        ReferralProgram,
        on_delete=models.CASCADE,
        related_name='referrals',
        verbose_name=_('Programme')
    )
    
    # Statistiques
    total_commission_earned = models.DecimalField(
        _('Commission totale gagnée'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    games_played = models.PositiveIntegerField(_('Parties jouées'), default=0)
    winning_games_count = models.PositiveIntegerField(
        _('Parties gagnantes ayant généré commission'),
        default=0,
        help_text=_('Compte uniquement les parties gagnantes')
    )
    last_commission_date = models.DateTimeField(_('Dernière commission'), null=True, blank=True)
    
    # État Premium
    status = models.CharField(_('Statut'), max_length=20, choices=STATUS_CHOICES, default='active')
    is_premium_referrer = models.BooleanField(
        _('Parrain premium'),
        default=False,
        help_text=_('Premium = 10% commission illimitée. Non-premium = 10% sur 3 premières parties gagnantes seulement')
    )
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        db_table = 'referrals'
        verbose_name = _('Parrainage')
        verbose_name_plural = _('Parrainages')
        unique_together = ['referrer', 'referred']
        indexes = [
            models.Index(fields=['referrer', 'status']),
            models.Index(fields=['referred']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.referrer.username} → {self.referred.username}"
    
    def can_earn_commission(self, game_won=True):
        """
        Vérifier si ce parrainage peut générer une commission.
        RÈGLES EXACTES :
        - Premium: 10% de commission sur TOUTES les parties gagnantes (illimité)
        - Non-premium: 10% de commission sur les 3 PREMIÈRES parties gagnantes SEULEMENT
        
        Args:
            game_won (bool): La partie a-t-elle été gagnée par le filleul?
        """
        # Les commissions ne s'appliquent que sur les parties gagnantes
        if not game_won:
            return False, _('Commission uniquement sur parties gagnantes')
        
        if self.status != 'active':
            return False, _('Parrainage inactif')
        
        if self.program.status != 'active':
            return False, _('Programme de parrainage inactif')
        
        # RÈGLE PREMIUM vs NON-PREMIUM
        if not self.is_premium_referrer:
            # Non-premium: max 3 parties gagnantes seulement
            if self.winning_games_count >= 3:
                return False, _('Limite de 3 parties gagnantes atteinte (parrain non-premium). Upgrade vers premium pour commission illimitée')
        
        return True, _('Commission autorisée')
    
    def _check_commission_limits(self):
        """Vérifier les limites de commission."""
        today = timezone.now().date()
        this_month_start = today.replace(day=1)
        
        # Limite quotidienne
        if self.program.max_daily_commission > 0:
            daily_commission = ReferralCommission.objects.filter(
                referral=self,
                created_at__date=today,
                status='completed'
            ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
            
            if daily_commission >= self.program.max_daily_commission:
                return False
        
        # Limite mensuelle
        if self.program.max_monthly_commission > 0:
            monthly_commission = ReferralCommission.objects.filter(
                referral=self,
                created_at__date__gte=this_month_start,
                status='completed'
            ).aggregate(total=models.Sum('amount'))['total'] or Decimal('0.00')
            
            if monthly_commission >= self.program.max_monthly_commission:
                return False
        
        return True
    
    def get_premium_status_display(self):
        """Afficher le statut premium avec les conditions applicables."""
        if self.is_premium_referrer:
            return "Premium (10% illimité)"
        else:
            remaining = max(0, 3 - self.winning_games_count)
            return f"Non-premium ({remaining} parties gagnantes restantes)"
    
    def calculate_commission(self, game_bet_amount, game_won=True, game_currency='FCFA'):
        """
        Calculer la commission pour une partie.
        
        FORMULE CORRECTE:
        1. La plateforme prélève 14% de la mise
        2. Le parrain reçoit 10% de cette commission plateforme
        3. Donc le parrain reçoit: 10% × 14% = 1.4% de la mise originale
        
        Args:
            game_bet_amount (Decimal): La MISE originale du filleul (pas les gains)
            game_won (bool): La partie a-t-elle été gagnée?
            game_currency (str): Devise
            
        Returns:
            tuple: (montant_commission, message)
        """
        from apps.core import BUSINESS_LIMITS
        
        can_earn, message = self.can_earn_commission(game_won=game_won)
        if not can_earn:
            return Decimal('0.00'), message
        
        # Formule: Parrain reçoit 10% de la commission plateforme (14%)
        # = game_bet_amount × 14% × 10% = game_bet_amount × 1.4%
        platform_commission_rate = Decimal(str(BUSINESS_LIMITS.get('PLATFORM_COMMISSION_RATE', 0.14)))
        parrain_rate = Decimal('10.00') / Decimal('100')  # 10%
        
        # Commission finale: 10% de la commission plateforme
        # = mise × taux_plateforme × taux_parrain
        commission = game_bet_amount * platform_commission_rate * parrain_rate
        
        # Arrondir à 2 décimales
        commission = commission.quantize(Decimal('0.01'))
        
        # Appliquer la limite maximale par filleul si elle existe
        if self.program.max_commission_per_referral > 0:
            remaining_limit = self.program.max_commission_per_referral - self.total_commission_earned
            commission = min(commission, remaining_limit)
        
        return max(Decimal('0.00'), commission), _('Commission calculée (10% de la commission plateforme 14%)')
    
    def _calculate_tiered_commission(self, game_amount):
        """Calculer la commission par paliers."""
        # Exemple de paliers (à personnaliser selon les besoins)
        tiers = [
            (Decimal('1000'), Decimal('5.00')),    # Jusqu'à 1000: 5%
            (Decimal('5000'), Decimal('7.50')),    # 1001-5000: 7.5%
            (Decimal('10000'), Decimal('10.00')),  # 5001-10000: 10%
            (Decimal('50000'), Decimal('12.50')),  # 10001-50000: 12.5%
            (float('inf'), Decimal('15.00')),      # 50000+: 15%
        ]
        
        for threshold, rate in tiers:
            if game_amount <= threshold:
                return game_amount * (rate / Decimal('100'))
        
        return game_amount * (self.program.commission_rate / Decimal('100'))
    
    def add_commission(self, game, amount, currency='FCFA'):
        """Ajouter une commission pour ce parrainage."""
        commission = ReferralCommission.objects.create(
            referral=self,
            game=game,
            amount=amount,
            currency=currency,
            referrer_balance_before=self.referrer.get_balance(currency),
            status='pending'
        )
        
        return commission
    
    def update_stats(self, game_won=False, commission_amount=None):
        """
        Mettre à jour les statistiques de parrainage.
        
        Args:
            game_won (bool): La partie a été gagnée?
            commission_amount (Decimal): Montant de la commission (si applicable)
        """
        self.games_played += 1
        
        # Incrémenter le compteur de parties gagnantes si applicable
        if game_won:
            if commission_amount and commission_amount > 0:
                self.winning_games_count += 1
                self.total_commission_earned += commission_amount
                self.last_commission_date = timezone.now()
        
        self.save()


class ReferralCommission(models.Model):
    """Commissions de parrainage."""
    
    STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('completed', _('Payée')),
        ('cancelled', _('Annulée')),
        ('failed', _('Échoué')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relations
    referral = models.ForeignKey(
        Referral,
        on_delete=models.CASCADE,
        related_name='commissions',
        verbose_name=_('Parrainage')
    )
    game = models.ForeignKey(
        'games.Game',
        on_delete=models.CASCADE,
        related_name='referral_commissions',
        verbose_name=_('Partie')
    )
    transaction = models.ForeignKey(
        'payments.Transaction',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='referral_commission',
        verbose_name=_('Transaction')
    )
    
    # Montants
    amount = models.DecimalField(
        _('Montant de la commission'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    currency = models.CharField(_('Devise'), max_length=5, default='FCFA')
    
    # État des soldes
    referrer_balance_before = models.DecimalField(
        _('Solde du parrain avant'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    referrer_balance_after = models.DecimalField(
        _('Solde du parrain après'),
        max_digits=12,
        decimal_places=2,
        null=True,
        blank=True
    )
    
    # État
    status = models.CharField(_('Statut'), max_length=20, choices=STATUS_CHOICES, default='pending')
    failure_reason = models.TextField(_('Raison de l\'échec'), blank=True)
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    processed_at = models.DateTimeField(_('Traité le'), null=True, blank=True)
    
    class Meta:
        db_table = 'referral_commissions'
        verbose_name = _('Commission de parrainage')
        verbose_name_plural = _('Commissions de parrainage')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['referral', 'created_at']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['game']),
        ]
    
    def __str__(self):
        return f"Commission {self.amount} {self.currency} - {self.referral.referrer.username}"
    
    def process_commission(self):
        """Traiter la commission de parrainage."""
        if self.status != 'pending':
            raise ValidationError(_('Cette commission a déjà été traitée'))
        
        try:
            # Créer une transaction pour la commission
            from apps.payments.models import Transaction
            
            transaction = Transaction.objects.create(
                user=self.referral.referrer,
                transaction_type='referral',
                amount=self.amount,
                currency=self.currency,
                status='pending',
                metadata={
                    'referral_id': str(self.referral.id),
                    'game_id': str(self.game.id),
                    'referred_user': self.referral.referred.username,
                }
            )
            
            # Traiter la transaction
            transaction.process()
            
            # Mettre à jour la commission
            self.transaction = transaction
            self.status = 'completed'
            self.processed_at = timezone.now()
            self.referrer_balance_after = self.referral.referrer.get_balance(self.currency)
            self.save()
            
            # Mettre à jour les statistiques du parrainage
            self.referral.update_stats(commission_amount=self.amount)
            
            return True
            
        except Exception as e:
            self.status = 'failed'
            self.failure_reason = str(e)
            self.save()
            raise


class PremiumSubscription(models.Model):
    """Abonnements premium pour le parrainage."""
    
    STATUS_CHOICES = [
        ('active', _('Actif')),
        ('expired', _('Expiré')),
        ('cancelled', _('Annulé')),
        ('suspended', _('Suspendu')),
    ]
    
    PLAN_TYPES = [
        ('monthly', _('Mensuel')),
        ('quarterly', _('Trimestriel')),
        ('yearly', _('Annuel')),
        ('lifetime', _('À vie')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relations
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='premium_subscriptions',
        verbose_name=_('Utilisateur')
    )
    transaction = models.ForeignKey(
        'payments.Transaction',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='premium_subscription',
        verbose_name=_('Transaction')
    )
    
    # Configuration
    plan_type = models.CharField(_('Type de plan'), max_length=20, choices=PLAN_TYPES)
    price = models.DecimalField(_('Prix'), max_digits=10, decimal_places=2)
    currency = models.CharField(_('Devise'), max_length=5, default='FCFA')
    
    # Dates
    start_date = models.DateTimeField(_('Date de début'))
    end_date = models.DateTimeField(_('Date de fin'), null=True, blank=True)
    auto_renewal = models.BooleanField(_('Renouvellement automatique'), default=False)
    
    # État
    status = models.CharField(_('Statut'), max_length=20, choices=STATUS_CHOICES, default='active')
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    cancelled_at = models.DateTimeField(_('Annulé le'), null=True, blank=True)
    
    class Meta:
        db_table = 'premium_subscriptions'
        verbose_name = _('Abonnement premium')
        verbose_name_plural = _('Abonnements premium')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['end_date', 'status']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_plan_type_display()} ({self.get_status_display()})"
    
    def save(self, *args, **kwargs):
        # ✅ Définir la date de début si elle n'existe pas
        if not self.start_date:
            self.start_date = timezone.now()
        
        # Calculer la date de fin selon le type de plan
        if not self.end_date and self.plan_type != 'lifetime':
            if self.plan_type == 'monthly':
                self.end_date = self.start_date + relativedelta(months=1)
            elif self.plan_type == 'quarterly':
                self.end_date = self.start_date + relativedelta(months=3)
            elif self.plan_type == 'yearly':
                self.end_date = self.start_date + relativedelta(years=1)
        
        super().save(*args, **kwargs)
        
        # Mettre à jour le statut premium des parrainages
        self.update_referral_premium_status()
    
    def update_referral_premium_status(self):
        """Mettre à jour le statut premium des parrainages."""
        is_premium = self.is_active()
        Referral.objects.filter(referrer=self.user).update(is_premium_referrer=is_premium)
    
    def is_active(self):
        """Vérifier si l'abonnement est actif."""
        if self.status != 'active':
            return False
        
        if self.plan_type == 'lifetime':
            return True
        
        if self.end_date and timezone.now() > self.end_date:
            self.status = 'expired'
            self.save()
            return False
        
        return True
    
    def cancel(self, reason='User cancelled'):
        """Annuler l'abonnement."""
        if self.status not in ['active', 'suspended']:
            raise ValidationError(_('Cet abonnement ne peut pas être annulé'))
        
        self.status = 'cancelled'
        self.cancelled_at = timezone.now()
        self.auto_renewal = False
        self.save()
        
        # Mettre à jour les parrainages
        self.update_referral_premium_status()
    
    def renew(self):
        """Renouveler l'abonnement."""
        if not self.auto_renewal:
            return False
        
        if self.plan_type == 'lifetime':
            return True
        
        # Créer un nouvel abonnement
        new_subscription = PremiumSubscription.objects.create(
            user=self.user,
            plan_type=self.plan_type,
            price=self.price,
            currency=self.currency,
            start_date=self.end_date,
            auto_renewal=self.auto_renewal,
            status='active'
        )
        
        # Désactiver l'ancien abonnement
        self.status = 'expired'
        self.save()
        
        return new_subscription


class ReferralStatistics(models.Model):
    """Statistiques agrégées de parrainage."""
    
    PERIOD_TYPES = [
        ('daily', _('Quotidien')),
        ('weekly', _('Hebdomadaire')),
        ('monthly', _('Mensuel')),
        ('yearly', _('Annuel')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='referral_statistics',
        verbose_name=_('Utilisateur')
    )
    
    period_type = models.CharField(_('Type de période'), max_length=20, choices=PERIOD_TYPES)
    period_start = models.DateField(_('Début de période'))
    period_end = models.DateField(_('Fin de période'))
    
    # Statistiques de base
    total_referrals = models.PositiveIntegerField(_('Total filleuls'), default=0)
    active_referrals = models.PositiveIntegerField(_('Filleuls actifs'), default=0)
    new_referrals = models.PositiveIntegerField(_('Nouveaux filleuls'), default=0)
    
    # Statistiques de jeu
    total_games_played = models.PositiveIntegerField(_('Parties jouées'), default=0)
    commission_games = models.PositiveIntegerField(_('Parties avec commission'), default=0)
    
    # Statistiques financières
    total_commission_earned = models.DecimalField(
        _('Commission totale'),
        max_digits=12,
        decimal_places=2,
        default=Decimal('0.00')
    )
    total_bet_volume = models.DecimalField(
        _('Volume de mises'),
        max_digits=15,
        decimal_places=2,
        default=Decimal('0.00')
    )
    average_commission_per_game = models.DecimalField(
        _('Commission moyenne par partie'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        db_table = 'referral_statistics'
        verbose_name = _('Statistiques de parrainage')
        verbose_name_plural = _('Statistiques de parrainage')
        unique_together = ['user', 'period_type', 'period_start']
        ordering = ['-period_start']
        indexes = [
            models.Index(fields=['user', 'period_type']),
            models.Index(fields=['period_start', 'period_end']),
        ]
    
    def __str__(self):
        return f"{self.user.username} - {self.get_period_type_display()} ({self.period_start})"
    
    @classmethod
    def calculate_statistics(cls, user, period_type, start_date, end_date):
        """Calculer les statistiques pour une période donnée."""
        
        # Obtenir ou créer l'objet statistiques
        stats, created = cls.objects.get_or_create(
            user=user,
            period_type=period_type,
            period_start=start_date,
            defaults={'period_end': end_date}
        )
        
        # Calculer les statistiques
        referrals = Referral.objects.filter(referrer=user)
        
        stats.total_referrals = referrals.count()
        stats.active_referrals = referrals.filter(status='active').count()
        stats.new_referrals = referrals.filter(
            created_at__date__gte=start_date,
            created_at__date__lte=end_date
        ).count()
        
        # Statistiques de commission
        commissions = ReferralCommission.objects.filter(
            referral__referrer=user,
            created_at__date__gte=start_date,
            created_at__date__lte=end_date,
            status='completed'
        )
        
        commission_data = commissions.aggregate(
            total=models.Sum('amount'),
            count=models.Count('id')
        )
        
        stats.total_commission_earned = commission_data['total'] or Decimal('0.00')
        stats.commission_games = commission_data['count'] or 0
        
        # Calculer la commission moyenne
        if stats.commission_games > 0:
            stats.average_commission_per_game = stats.total_commission_earned / stats.commission_games
        else:
            stats.average_commission_per_game = Decimal('0.00')
        
        # Volume de mises (approximation basée sur les commissions)
        if stats.total_commission_earned > 0:
            # Estimer le volume basé sur le taux de commission moyen (10%)
            estimated_volume = stats.total_commission_earned / Decimal('0.10')
            stats.total_bet_volume = estimated_volume
        
        stats.save()
        return stats


class ReferralBonus(models.Model):
    """Bonus de parrainage."""
    
    BONUS_TYPES = [
        ('signup', _('Bonus d\'inscription')),
        ('first_deposit', _('Premier dépôt')),
        ('milestone', _('Palier atteint')),
        ('loyalty', _('Fidélité')),
        ('special', _('Événement spécial')),
    ]
    
    STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('approved', _('Approuvé')),
        ('claimed', _('Réclamé')),
        ('expired', _('Expiré')),
        ('cancelled', _('Annulé')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relations
    referral = models.ForeignKey(
        Referral,
        on_delete=models.CASCADE,
        related_name='bonuses',
        verbose_name=_('Parrainage')
    )
    transaction = models.ForeignKey(
        'payments.Transaction',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='referral_bonus',
        verbose_name=_('Transaction')
    )
    
    # Détails du bonus
    bonus_type = models.CharField(_('Type de bonus'), max_length=20, choices=BONUS_TYPES)
    amount = models.DecimalField(_('Montant'), max_digits=10, decimal_places=2)
    currency = models.CharField(_('Devise'), max_length=5, default='FCFA')
    
    # Conditions
    minimum_bet_requirement = models.DecimalField(
        _('Mise minimum requise'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    wagering_requirement = models.PositiveIntegerField(
        _('Exigence de mise (x fois)'),
        default=1,
        help_text=_('Nombre de fois que le bonus doit être misé')
    )
    
    # État
    status = models.CharField(_('Statut'), max_length=20, choices=STATUS_CHOICES, default='pending')
    description = models.TextField(_('Description'), blank=True)
    
    # Dates
    expires_at = models.DateTimeField(_('Expire le'), null=True, blank=True)
    claimed_at = models.DateTimeField(_('Réclamé le'), null=True, blank=True)
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        db_table = 'referral_bonuses'
        verbose_name = _('Bonus de parrainage')
        verbose_name_plural = _('Bonus de parrainage')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"{self.get_bonus_type_display()} - {self.amount} {self.currency}"
    
    def can_claim(self):
        """Vérifier si le bonus peut être réclamé."""
        if self.status != 'approved':
            return False, _('Bonus non approuvé')
        
        if self.expires_at and timezone.now() > self.expires_at:
            self.status = 'expired'
            self.save()
            return False, _('Bonus expiré')
        
        return True, _('Bonus réclamable')
    
    def claim(self):
        """Réclamer le bonus."""
        can_claim, message = self.can_claim()
        if not can_claim:
            raise ValidationError(message)
        
        # Créer une transaction pour le bonus
        from apps.payments.models import Transaction
        
        transaction = Transaction.objects.create(
            user=self.referral.referrer,
            transaction_type='bonus',
            amount=self.amount,
            currency=self.currency,
            status='pending',
            metadata={
                'bonus_id': str(self.id),
                'bonus_type': self.bonus_type,
                'referral_id': str(self.referral.id),
            }
        )
        
        # Traiter la transaction
        transaction.process()
        
        # Mettre à jour le bonus
        self.transaction = transaction
        self.status = 'claimed'
        self.claimed_at = timezone.now()
        self.save()
        
        return transaction


class ReferralCode(models.Model):
    """Codes de parrainage partageables avec tracking."""
    
    SHARE_CHANNEL_CHOICES = [
        ('whatsapp', _('WhatsApp')),
        ('telegram', _('Telegram')),
        ('facebook', _('Facebook')),
        ('twitter', _('Twitter')),
        ('instagram', _('Instagram')),
        ('email', _('Email')),
        ('sms', _('SMS')),
        ('direct', _('Lien direct')),
        ('other', _('Autre')),
    ]
    
    STATUS_CHOICES = [
        ('active', _('Actif')),
        ('inactive', _('Inactif')),
        ('expired', _('Expiré')),
        ('suspended', _('Suspendu')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Relations
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='referral_codes',
        verbose_name=_('Utilisateur')
    )
    
    program = models.ForeignKey(
        ReferralProgram,
        on_delete=models.CASCADE,
        related_name='codes',
        verbose_name=_('Programme')
    )
    
    # Code
    code = models.CharField(
        _('Code'),
        max_length=20,
        unique=True,
        db_index=True,
        help_text=_('Code unique pour le parrainage')
    )
    
    # URL partageables
    share_url = models.URLField(
        _('URL du code'),
        help_text=_('URL complet pour partager le code'),
        blank=True
    )
    
    # Partages
    share_channels = models.CharField(
        _('Canaux de partage'),
        max_length=255,
        help_text=_('Canaux par lesquels ce code a été partagé'),
        blank=True
    )
    
    # Limites
    max_uses = models.PositiveIntegerField(
        _('Utilisations maximales'),
        default=0,
        help_text=_('0 = illimité')
    )
    current_uses = models.PositiveIntegerField(
        _('Utilisations actuelles'),
        default=0
    )
    
    # Conditions d'activation
    min_first_deposit = models.DecimalField(
        _('Dépôt minimum pour activation'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text=_('Montant minimum à déposer après inscription via le code')
    )
    
    # Bonus associé
    bonus_on_signup = models.DecimalField(
        _('Bonus à l\'inscription'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00'),
        help_text=_('Bonus octroyé au nouveau joueur qui utilise ce code')
    )
    
    # État
    status = models.CharField(
        _('Statut'),
        max_length=20,
        choices=STATUS_CHOICES,
        default='active'
    )
    
    # Dates
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    expires_at = models.DateTimeField(
        _('Expire le'),
        null=True,
        blank=True,
        help_text=_('Laissez vide pour pas de date d\'expiration')
    )
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    # Métadonnées
    is_primary = models.BooleanField(
        _('Code principal'),
        default=False,
        help_text=_('Le code utilisé par défaut pour ce parrain')
    )
    
    description = models.TextField(_('Description'), blank=True)
    
    class Meta:
        db_table = 'referral_codes'
        verbose_name = _('Code de parrainage')
        verbose_name_plural = _('Codes de parrainage')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'status']),
            models.Index(fields=['code']),
            models.Index(fields=['created_at']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.user.username}"
    
    def save(self, *args, **kwargs):
        # Générer le code s'il n'existe pas
        if not self.code:
            self.code = self.generate_code()
        
        # S'assurer qu'un seul code principal par utilisateur
        if self.is_primary and self.status == 'active':
            ReferralCode.objects.filter(
                user=self.user,
                is_primary=True
            ).exclude(id=self.id).update(is_primary=False)
        
        super().save(*args, **kwargs)
    
    @staticmethod
    def generate_code(length=8):
        """Générer un code unique."""
        characters = string.ascii_uppercase + string.digits
        # Exclure les caractères ambigus (I, O, 1, 0)
        characters = characters.replace('I', '').replace('O', '').replace('0', '')
        
        code = ''.join(secrets.choice(characters) for _ in range(length))
        
        # S'assurer qu'il est unique
        while ReferralCode.objects.filter(code=code).exists():
            code = ''.join(secrets.choice(characters) for _ in range(length))
        
        return code
    
    def is_valid(self):
        """Vérifier si le code est valide."""
        if self.status != 'active':
            return False, _('Code inactif')
        
        if self.expires_at and timezone.now() > self.expires_at:
            self.status = 'expired'
            self.save()
            return False, _('Code expiré')
        
        if self.max_uses > 0 and self.current_uses >= self.max_uses:
            return False, _('Nombre d\'utilisations dépassé')
        
        if not self.user.is_active:
            return False, _('Parrain inactif')
        
        return True, _('Code valide')
    
    def can_be_used(self):
        """Alias pour is_valid()."""
        return self.is_valid()
    
    def use_code(self):
        """Incrémenter le compteur d'utilisation."""
        self.current_uses += 1
        self.save()
    
    def get_share_links(self, base_url=None):
        """Obtenir les liens de partage pour différents canaux."""
        if not base_url:
            base_url = settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else 'https://app.example.com'
        
        signup_url = f"{base_url}/signup?ref={self.code}"
        
        links = {
            'whatsapp': f"https://wa.me/?text={self._urlencode(f'Rejoins-moi sur RumoRush avec mon code de parrainage: {self.code} {signup_url}')}",
            'telegram': f"https://t.me/share/url?url={self._urlencode(signup_url)}&text={self._urlencode(f'Code de parrainage: {self.code}')}",
            'facebook': f"https://www.facebook.com/sharer/sharer.php?u={self._urlencode(signup_url)}",
            'twitter': f"https://twitter.com/intent/tweet?text={self._urlencode(f'Rejoins-moi sur RumoRush! Code: {self.code}')} {self._urlencode(signup_url)}",
            'email': f"mailto:?subject={self._urlencode('Invitation RumoRush')}&body={self._urlencode(f'Rejoins-moi sur RumoRush!\\n\\nCode: {self.code}\\n\\n{signup_url}')}",
            'direct': signup_url,
        }
        
        return links
    
    @staticmethod
    def _urlencode(text):
        """Encoder le texte pour les URLs."""
        import urllib.parse
        return urllib.parse.quote(text)
    
    def get_share_link(self, channel='direct', base_url=None):
        """Obtenir le lien de partage pour un canal spécifique."""
        links = self.get_share_links(base_url)
        return links.get(channel, links['direct'])
    
    def get_qr_code_url(self, base_url=None):
        """Obtenir l'URL du QR code."""
        if not base_url:
            base_url = settings.FRONTEND_URL if hasattr(settings, 'FRONTEND_URL') else 'https://app.example.com'
        
        # Supposant que vous avez un endpoint pour générer les QR codes
        return f"{base_url}/api/referrals/codes/{self.id}/qrcode/"
    
    def log_share(self, channel):
        """Enregistrer un partage sur un canal."""
        if channel not in dict(self.SHARE_CHANNEL_CHOICES):
            channel = 'other'
        
        channels = self.share_channels.split(',') if self.share_channels else []
        if channel not in channels:
            channels.append(channel)
            self.share_channels = ','.join(channels)
            self.save()
        
        # Créer un log de partage
        ReferralCodeShare.objects.create(
            code=self,
            channel=channel
        )
    
    def get_conversion_rate(self):
        """Calculer le taux de conversion (utilisations / partages)."""
        total_shares = self.shares.count()
        if total_shares == 0:
            return 0.0
        
        return (self.current_uses / total_shares) * 100


class ReferralCodeShare(models.Model):
    """Logs de partage des codes de parrainage."""
    
    CHANNEL_CHOICES = ReferralCode.SHARE_CHANNEL_CHOICES
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    code = models.ForeignKey(
        ReferralCode,
        on_delete=models.CASCADE,
        related_name='shares',
        verbose_name=_('Code')
    )
    
    channel = models.CharField(
        _('Canal'),
        max_length=20,
        choices=CHANNEL_CHOICES
    )
    
    shared_by_ip = models.GenericIPAddressField(
        _('IP du partage'),
        null=True,
        blank=True
    )
    
    user_agent = models.TextField(
        _('User Agent'),
        blank=True
    )
    
    shared_at = models.DateTimeField(
        _('Partagé le'),
        auto_now_add=True
    )
    
    class Meta:
        db_table = 'referral_code_shares'
        verbose_name = _('Partage de code')
        verbose_name_plural = _('Partages de codes')
        ordering = ['-shared_at']
        indexes = [
            models.Index(fields=['code', 'shared_at']),
            models.Index(fields=['channel']),
        ]
    
    def __str__(self):
        return f"{self.code.code} shared on {self.channel}"


class ReferralCodeClick(models.Model):
    """Tracking des clics sur les liens de parrainage."""
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    code = models.ForeignKey(
        ReferralCode,
        on_delete=models.CASCADE,
        related_name='clicks',
        verbose_name=_('Code')
    )
    
    clicked_at = models.DateTimeField(
        _('Cliqué le'),
        auto_now_add=True
    )
    
    visitor_ip = models.GenericIPAddressField(
        _('IP du visiteur'),
        null=True,
        blank=True
    )
    
    user_agent = models.TextField(
        _('User Agent'),
        blank=True
    )
    
    referrer = models.CharField(
        _('Provenance'),
        max_length=500,
        blank=True,
        help_text=_('Où le clic venait')
    )
    
    # Conversion
    converted_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='referral_codes_converted_from',
        verbose_name=_('Utilisateur converti')
    )
    
    converted_at = models.DateTimeField(
        _('Converti le'),
        null=True,
        blank=True
    )
    
    class Meta:
        db_table = 'referral_code_clicks'
        verbose_name = _('Clic sur code')
        verbose_name_plural = _('Clics sur codes')
        ordering = ['-clicked_at']
        indexes = [
            models.Index(fields=['code', 'clicked_at']),
            models.Index(fields=['converted_user']),
        ]
    
    def __str__(self):
        return f"Click on {self.code.code} at {self.clicked_at}"
    
    def track_conversion(self, user):
        """Enregistrer la conversion."""
        self.converted_user = user
        self.converted_at = timezone.now()
        self.save()
        
        # Incrémenter le compteur d'utilisation du code si c'est une nouvelle conversion
        if self.code.current_uses == 0 or self.code.current_uses < ReferralCodeClick.objects.filter(
            code=self.code,
            converted_user__isnull=False
        ).count():
            self.code.use_code()
