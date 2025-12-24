# apps/referrals/serializers.py
# ==============================

from rest_framework import serializers
from rest_framework.validators import UniqueTogetherValidator
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.contrib.auth import get_user_model
from decimal import Decimal
from .models import (
    ReferralProgram, Referral, ReferralCommission,
    PremiumSubscription, ReferralStatistics, ReferralBonus,
    ReferralCode, ReferralCodeShare, ReferralCodeClick
)
from . import PREMIUM_PLANS

User = get_user_model()


class ReferralProgramSerializer(serializers.ModelSerializer):
    """Serializer pour les programmes de parrainage."""
    
    total_referrals = serializers.SerializerMethodField()
    total_commissions_paid = serializers.SerializerMethodField()
    average_commission_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = ReferralProgram
        fields = [
            'id', 'name', 'description', 'commission_type', 'commission_rate',
            'fixed_commission', 'max_commission_per_referral', 'max_daily_commission',
            'max_monthly_commission', 'min_bet_for_commission', 'free_games_limit',
            'status', 'is_default', 'created_at', 'updated_at',
            'total_referrals', 'total_commissions_paid', 'average_commission_rate'
        ]
        read_only_fields = ['created_at', 'updated_at', 'total_referrals', 
                           'total_commissions_paid', 'average_commission_rate']
    
    def get_total_referrals(self, obj):
        """Nombre total de parrainages actifs dans ce programme."""
        return obj.referrals.filter(status='active').count()
    
    def get_total_commissions_paid(self, obj):
        """Total des commissions payées pour ce programme."""
        return obj.referrals.aggregate(
            total=serializers.models.Sum(
                'commissions__amount',
                filter=serializers.models.Q(commissions__status='completed')
            )
        )['total'] or Decimal('0.00')
    
    def get_average_commission_rate(self, obj):
        """Taux de commission moyen effectif."""
        if obj.commission_type == 'percentage':
            return float(obj.commission_rate)
        # Pour les autres types, calculer une moyenne basée sur les commissions réelles
        commissions = obj.referrals.filter(
            commissions__status='completed'
        ).aggregate(
            total_commission=serializers.models.Sum('commissions__amount'),
            total_games=serializers.models.Count('commissions')
        )
        
        if commissions['total_games'] > 0:
            avg_commission = commissions['total_commission'] / commissions['total_games']
            # Estimer le taux basé sur une mise moyenne (approximation)
            estimated_rate = (avg_commission / Decimal('1000')) * 100
            return min(float(estimated_rate), 50.0)  # Cap à 50%
        
        return 0.0
    
    def validate_commission_rate(self, value):
        """Valider le taux de commission."""
        if value <= 0 or value > 50:
            raise serializers.ValidationError(
                _("Le taux de commission doit être entre 0.01% et 50%")
            )
        return value
    
    def validate(self, attrs):
        """Validation globale du programme."""
        commission_type = attrs.get('commission_type')
        commission_rate = attrs.get('commission_rate')
        fixed_commission = attrs.get('fixed_commission')
        
        if commission_type == 'fixed' and (not fixed_commission or fixed_commission <= 0):
            raise serializers.ValidationError({
                'fixed_commission': _("Commission fixe requise pour ce type")
            })
        
        if commission_type in ['percentage', 'tiered'] and (not commission_rate or commission_rate <= 0):
            raise serializers.ValidationError({
                'commission_rate': _("Taux de commission requis pour ce type")
            })
        
        return attrs


class UserBasicSerializer(serializers.ModelSerializer):
    """Serializer basique pour les utilisateurs dans les parrainages."""
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'date_joined']
        read_only_fields = ['id', 'date_joined']


class ReferralSerializer(serializers.ModelSerializer):
    """Serializer pour les parrainages."""
    
    referrer = UserBasicSerializer(read_only=True)
    referred = UserBasicSerializer(read_only=True)
    program = ReferralProgramSerializer(read_only=True)
    
    # Champs calculés
    commission_rate_effective = serializers.SerializerMethodField()
    games_played_this_month = serializers.SerializerMethodField()
    commission_this_month = serializers.SerializerMethodField()
    next_milestone = serializers.SerializerMethodField()
    can_earn_commission = serializers.SerializerMethodField()
    
    class Meta:
        model = Referral
        fields = [
            'id', 'referrer', 'referred', 'program', 'total_commission_earned',
            'games_played', 'commission_games_count', 'last_commission_date',
            'status', 'is_premium_referrer', 'created_at', 'updated_at',
            'commission_rate_effective', 'games_played_this_month',
            'commission_this_month', 'next_milestone', 'can_earn_commission'
        ]
        read_only_fields = [
            'total_commission_earned', 'games_played', 'commission_games_count',
            'last_commission_date', 'created_at', 'updated_at'
        ]
    
    def get_commission_rate_effective(self, obj):
        """Taux de commission effectif selon le type de programme."""
        if obj.program.commission_type == 'percentage':
            return float(obj.program.commission_rate)
        elif obj.program.commission_type == 'fixed':
            return float(obj.program.fixed_commission)
        else:  # tiered
            # Retourner le taux du premier palier
            return 5.0  # Valeur par défaut
    
    def get_games_played_this_month(self, obj):
        """Nombre de parties jouées ce mois par le filleul."""
        from datetime import date
        current_month = date.today().replace(day=1)
        
        return obj.commissions.filter(
            created_at__date__gte=current_month
        ).count()
    
    def get_commission_this_month(self, obj):
        """Commission gagnée ce mois."""
        from datetime import date
        current_month = date.today().replace(day=1)
        
        commission = obj.commissions.filter(
            created_at__date__gte=current_month,
            status='completed'
        ).aggregate(
            total=serializers.models.Sum('amount')
        )['total']
        
        return float(commission or Decimal('0.00'))
    
    def get_next_milestone(self, obj):
        """Prochain palier à atteindre."""
        current_games = obj.commission_games_count
        milestones = [10, 25, 50, 100, 250, 500, 1000]
        
        for milestone in milestones:
            if current_games < milestone:
                return {
                    'games_target': milestone,
                    'games_remaining': milestone - current_games,
                    'progress_percentage': (current_games / milestone) * 100
                }
        
        return None
    
    def get_can_earn_commission(self, obj):
        """Vérifier si ce parrainage peut encore générer des commissions."""
        can_earn, message = obj.can_earn_commission(Decimal('1000'))  # Test avec 1000 FCFA
        return {
            'status': can_earn,
            'message': str(message),
            'remaining_free_games': max(0, obj.program.free_games_limit - obj.commission_games_count) if not obj.is_premium_referrer else None
        }


class CreateReferralSerializer(serializers.Serializer):
    """Serializer pour créer un nouveau parrainage."""
    
    referral_code = serializers.CharField(max_length=50, required=False)
    referred_user_id = serializers.UUIDField(required=False)
    referred_username = serializers.CharField(max_length=150, required=False)
    program_id = serializers.UUIDField(required=False)
    
    def validate(self, attrs):
        """Valider les données de création du parrainage."""
        referral_code = attrs.get('referral_code')
        referred_user_id = attrs.get('referred_user_id')
        referred_username = attrs.get('referred_username')
        
        # Au moins un moyen d'identifier le filleul
        if not any([referral_code, referred_user_id, referred_username]):
            raise serializers.ValidationError(
                _("Code de parrainage, ID utilisateur ou nom d'utilisateur requis")
            )
        
        # Identifier l'utilisateur filleul
        referred_user = None
        
        if referred_user_id:
            try:
                referred_user = User.objects.get(id=referred_user_id)
            except User.DoesNotExist:
                raise serializers.ValidationError({
                    'referred_user_id': _("Utilisateur introuvable")
                })
        
        elif referred_username:
            try:
                referred_user = User.objects.get(username=referred_username)
            except User.DoesNotExist:
                raise serializers.ValidationError({
                    'referred_username': _("Nom d'utilisateur introuvable")
                })
        
        elif referral_code:
            # Décoder le code de parrainage pour trouver l'utilisateur
            try:
                # Supposons un format simple: "USER_{user_id}"
                if referral_code.startswith('USER_'):
                    user_id = referral_code.split('_')[1]
                    referred_user = User.objects.get(id=user_id)
                else:
                    raise serializers.ValidationError({
                        'referral_code': _("Code de parrainage invalide")
                    })
            except (IndexError, ValueError, User.DoesNotExist):
                raise serializers.ValidationError({
                    'referral_code': _("Code de parrainage invalide")
                })
        
        attrs['referred_user'] = referred_user
        return attrs


class ReferralCommissionSerializer(serializers.ModelSerializer):
    """Serializer pour les commissions de parrainage."""
    
    referrer_username = serializers.CharField(source='referral.referrer.username', read_only=True)
    referred_username = serializers.CharField(source='referral.referred.username', read_only=True)
    game_type = serializers.CharField(source='game.game_type', read_only=True)
    game_bet_amount = serializers.DecimalField(source='game.bet_amount', max_digits=10, decimal_places=2, read_only=True)
    
    class Meta:
        model = ReferralCommission
        fields = [
            'id', 'referrer_username', 'referred_username', 'game_type', 'game_bet_amount',
            'amount', 'currency', 'referrer_balance_before', 'referrer_balance_after',
            'status', 'failure_reason', 'created_at', 'processed_at'
        ]
        read_only_fields = [
            'referrer_balance_before', 'referrer_balance_after', 
            'created_at', 'processed_at'
        ]


class PremiumSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer pour les abonnements premium."""
    
    user = UserBasicSerializer(read_only=True)
    is_active = serializers.SerializerMethodField()
    days_remaining = serializers.SerializerMethodField()
    renewal_date = serializers.SerializerMethodField()
    benefits = serializers.SerializerMethodField()
    
    class Meta:
        model = PremiumSubscription
        fields = [
            'id', 'user', 'plan_type', 'price', 'currency', 'start_date',
            'end_date', 'auto_renewal', 'status', 'created_at', 'updated_at',
            'cancelled_at', 'is_active', 'days_remaining', 'renewal_date', 'benefits'
        ]
        read_only_fields = ['created_at', 'updated_at', 'cancelled_at']
    
    def get_is_active(self, obj):
        """Vérifier si l'abonnement est actif."""
        return obj.is_active()
    
    def get_days_remaining(self, obj):
        """Jours restants avant expiration."""
        if obj.plan_type == 'lifetime':
            return None
        
        if obj.end_date and obj.status == 'active':
            remaining = (obj.end_date.date() - timezone.now().date()).days
            return max(0, remaining)
        
        return 0
    
    def get_renewal_date(self, obj):
        """Date de renouvellement automatique."""
        if obj.auto_renewal and obj.end_date:
            return obj.end_date
        return None
    
    def get_benefits(self, obj):
        """Avantages de l'abonnement premium."""
        return {
            'unlimited_commissions': True,
            'higher_commission_limits': True,
            'exclusive_bonuses': True,
            'priority_support': True,
            'advanced_statistics': True,
            'custom_referral_codes': True
        }


class CreatePremiumSubscriptionSerializer(serializers.Serializer):
    """Serializer pour créer un abonnement premium."""
    
    plan_type = serializers.ChoiceField(choices=PremiumSubscription.PLAN_TYPES)
    currency = serializers.ChoiceField(choices=['FCFA', 'EUR', 'USD'], default='FCFA', required=False)
    auto_renewal = serializers.BooleanField(default=False, required=False)
    payment_method = serializers.CharField(max_length=50, required=False)
    
    def validate(self, attrs):
        """Valider la création d'abonnement."""
        plan_type = attrs['plan_type']
        currency = attrs.get('currency', 'FCFA')
        
        # Calculer le prix selon le plan et la devise
        if plan_type not in PREMIUM_PLANS:
            raise serializers.ValidationError({
                'plan_type': _("Type de plan invalide")
            })
        
        plan_config = PREMIUM_PLANS[plan_type]
        price_key = f'price_{currency.lower()}'
        
        if price_key not in plan_config:
            raise serializers.ValidationError({
                'currency': _("Devise non supportée pour ce plan")
            })
        
        attrs['price'] = Decimal(str(plan_config[price_key]))
        attrs['currency'] = currency
        attrs['duration_months'] = plan_config.get('duration_months', 1)
        
        return attrs


class ReferralStatisticsSerializer(serializers.ModelSerializer):
    """Serializer pour les statistiques de parrainage."""
    
    conversion_rate = serializers.SerializerMethodField()
    average_games_per_referral = serializers.SerializerMethodField()
    performance_trend = serializers.SerializerMethodField()
    
    class Meta:
        model = ReferralStatistics
        fields = [
            'id', 'period_type', 'period_start', 'period_end',
            'total_referrals', 'active_referrals', 'new_referrals',
            'total_games_played', 'commission_games', 'total_commission_earned',
            'total_bet_volume', 'average_commission_per_game',
            'conversion_rate', 'average_games_per_referral', 'performance_trend',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_conversion_rate(self, obj):
        """Taux de conversion (filleuls actifs / total filleuls)."""
        if obj.total_referrals > 0:
            return (obj.active_referrals / obj.total_referrals) * 100
        return 0.0
    
    def get_average_games_per_referral(self, obj):
        """Nombre moyen de parties par filleul."""
        if obj.active_referrals > 0:
            return obj.total_games_played / obj.active_referrals
        return 0.0
    
    def get_performance_trend(self, obj):
        """Tendance de performance (comparaison avec période précédente)."""
        try:
            # Chercher la période précédente
            if obj.period_type == 'daily':
                previous_period = obj.period_start - timezone.timedelta(days=1)
            elif obj.period_type == 'weekly':
                previous_period = obj.period_start - timezone.timedelta(weeks=1)
            elif obj.period_type == 'monthly':
                previous_period = obj.period_start - timezone.timedelta(days=30)
            else:
                previous_period = obj.period_start - timezone.timedelta(days=365)
            
            previous_stats = ReferralStatistics.objects.filter(
                user=obj.user,
                period_type=obj.period_type,
                period_start=previous_period
            ).first()
            
            if previous_stats and previous_stats.total_commission_earned > 0:
                change = ((obj.total_commission_earned - previous_stats.total_commission_earned) 
                         / previous_stats.total_commission_earned) * 100
                
                return {
                    'change_percentage': round(float(change), 2),
                    'trend': 'up' if change > 0 else 'down' if change < 0 else 'stable',
                    'previous_commission': float(previous_stats.total_commission_earned)
                }
            
        except Exception:
            pass
        
        return {
            'change_percentage': 0.0,
            'trend': 'stable',
            'previous_commission': 0.0
        }


class ReferralBonusSerializer(serializers.ModelSerializer):
    """Serializer pour les bonus de parrainage."""
    
    referrer_username = serializers.CharField(source='referral.referrer.username', read_only=True)
    referred_username = serializers.CharField(source='referral.referred.username', read_only=True)
    can_claim = serializers.SerializerMethodField()
    claim_requirements = serializers.SerializerMethodField()
    
    class Meta:
        model = ReferralBonus
        fields = [
            'id', 'referrer_username', 'referred_username', 'bonus_type',
            'amount', 'currency', 'minimum_bet_requirement', 'wagering_requirement',
            'status', 'description', 'expires_at', 'claimed_at',
            'created_at', 'updated_at', 'can_claim', 'claim_requirements'
        ]
        read_only_fields = ['created_at', 'updated_at', 'claimed_at']
    
    def get_can_claim(self, obj):
        """Vérifier si le bonus peut être réclamé."""
        can_claim, message = obj.can_claim()
        return {
            'status': can_claim,
            'message': str(message)
        }
    
    def get_claim_requirements(self, obj):
        """Conditions pour réclamer le bonus."""
        return {
            'minimum_bet': float(obj.minimum_bet_requirement),
            'wagering_multiplier': obj.wagering_requirement,
            'expires_at': obj.expires_at,
            'status': obj.status,
            'can_expire': obj.expires_at is not None
        }


class DashboardSerializer(serializers.Serializer):
    """Serializer pour le tableau de bord de parrainage."""
    
    total_referrals = serializers.IntegerField()
    active_referrals = serializers.IntegerField()
    total_commission_earned = serializers.DecimalField(max_digits=12, decimal_places=2)
    commission_this_month = serializers.DecimalField(max_digits=12, decimal_places=2)
    pending_commissions = serializers.DecimalField(max_digits=12, decimal_places=2)
    premium_status = serializers.BooleanField()
    referral_code = serializers.CharField()
    commission_rate = serializers.FloatField()
    
    # Statistiques détaillées
    stats = serializers.DictField()
    recent_commissions = ReferralCommissionSerializer(many=True)
    top_referrals = ReferralSerializer(many=True)
    available_bonuses = ReferralBonusSerializer(many=True)
    
    class Meta:
        fields = [
            'total_referrals', 'active_referrals', 'total_commission_earned',
            'commission_this_month', 'pending_commissions', 'premium_status',
            'referral_code', 'commission_rate', 'stats', 'recent_commissions',
            'top_referrals', 'available_bonuses'
        ]


class ReferralCodeClickSerializer(serializers.ModelSerializer):
    """Serializer pour ReferralCodeClick."""
    
    converted_user_username = serializers.CharField(
        source='converted_user.username',
        read_only=True,
        allow_null=True
    )
    
    class Meta:
        model = ReferralCodeClick
        fields = [
            'id', 'clicked_at', 'visitor_ip', 'converted_user_username',
            'converted_at', 'referrer'
        ]
        read_only_fields = ['id', 'clicked_at', 'visitor_ip', 'converted_at']


class ReferralCodeShareSerializer(serializers.ModelSerializer):
    """Serializer pour ReferralCodeShare."""
    
    class Meta:
        model = ReferralCodeShare
        fields = [
            'id', 'code', 'channel', 'share_count',
            'click_count', 'conversion_count', 'shared_at'
        ]
        read_only_fields = ['id', 'code', 'shared_at', 'share_count', 'click_count', 'conversion_count']


class ReferralCodeListSerializer(serializers.ModelSerializer):
    """Serializer simple pour lister les codes de parrainage."""
    
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    
    total_clicks = serializers.SerializerMethodField()
    total_conversions = serializers.SerializerMethodField()
    conversion_rate = serializers.SerializerMethodField()
    is_active = serializers.SerializerMethodField()
    
    class Meta:
        model = ReferralCode
        fields = [
            'id', 'code', 'status', 'status_display',
            'share_url', 'max_uses', 'current_uses',
            'expires_at', 'is_active', 'created_at',
            'total_clicks', 'total_conversions', 'conversion_rate'
        ]
        read_only_fields = fields
    
    def get_total_clicks(self, obj):
        """Obtenir le nombre total de clics."""
        return obj.clicks.count()
    
    def get_total_conversions(self, obj):
        """Obtenir le nombre total de conversions."""
        return obj.clicks.filter(converted_user__isnull=False).count()
    
    def get_conversion_rate(self, obj):
        """Obtenir le taux de conversion."""
        total_clicks = obj.clicks.count()
        if total_clicks == 0:
            return 0
        conversions = obj.clicks.filter(converted_user__isnull=False).count()
        return round((conversions / total_clicks) * 100, 2)
    
    def get_is_active(self, obj):
        """Vérifier si le code est actif."""
        return obj.status == 'active'


class ReferralCodeDetailSerializer(serializers.ModelSerializer):
    """Serializer complet pour ReferralCode."""
    
    status_display = serializers.CharField(
        source='get_status_display',
        read_only=True
    )
    
    shares = ReferralCodeShareSerializer(
        source='shares.all',
        many=True,
        read_only=True
    )
    
    recent_clicks = serializers.SerializerMethodField(read_only=True)
    recent_conversions = serializers.SerializerMethodField(read_only=True)
    
    # Statistiques
    total_clicks = serializers.SerializerMethodField()
    total_conversions = serializers.SerializerMethodField()
    total_commission_generated = serializers.SerializerMethodField()
    conversion_rate = serializers.SerializerMethodField()
    
    class Meta:
        model = ReferralCode
        fields = [
            'id', 'code', 'status', 'status_display',
            'full_url', 'short_url', 'max_uses', 'current_uses',
            'expiration_date', 'is_active', 'created_at', 'updated_at',
            'shares', 'recent_clicks', 'recent_conversions',
            'total_clicks', 'total_conversions', 'conversion_rate',
            'total_commission_generated'
        ]
        read_only_fields = [
            'id', 'code', 'created_at', 'updated_at', 'shares',
            'recent_clicks', 'recent_conversions', 'total_clicks',
            'total_conversions', 'conversion_rate', 'total_commission_generated'
        ]
    
    def get_recent_clicks(self, obj):
        """Obtenir les clics récents (derniers 10)."""
        recent = obj.clicks.all()[:10]
        return ReferralCodeClickSerializer(recent, many=True).data
    
    def get_recent_conversions(self, obj):
        """Obtenir les conversions récentes."""
        recent = obj.clicks.filter(converted_user__isnull=False).all()[:5]
        return ReferralCodeClickSerializer(recent, many=True).data
    
    def get_total_clicks(self, obj):
        """Obtenir le nombre total de clics."""
        return obj.clicks.count()
    
    def get_total_conversions(self, obj):
        """Obtenir le nombre total de conversions."""
        return obj.clicks.filter(converted_user__isnull=False).count()
    
    def get_conversion_rate(self, obj):
        """Obtenir le taux de conversion."""
        total_clicks = obj.clicks.count()
        if total_clicks == 0:
            return 0.0
        
        conversions = obj.clicks.filter(converted_user__isnull=False).count()
        return round((conversions / total_clicks) * 100, 2)
    
    def get_total_commission_generated(self, obj):
        """Obtenir la commission totale générée."""
        total = obj.get_total_commission_generated()
        return str(total)


class ReferralCodeCreateSerializer(serializers.Serializer):
    """Serializer pour créer un ReferralCode."""
    
    max_uses = serializers.IntegerField(
        required=False,
        default=1000,
        min_value=1,
        help_text=_('Nombre maximum d\'utilisations (0 = illimité)')
    )
    
    expiration_date = serializers.DateTimeField(
        required=False,
        allow_null=True,
        help_text=_('Date d\'expiration du code')
    )
    
    def validate(self, data):
        """Valider les données."""
        expiration = data.get('expiration_date')
        
        if expiration and expiration <= timezone.now():
            raise serializers.ValidationError(
                _('La date d\'expiration doit être dans le futur.')
            )
        
        return data


class ReferralLinkShareSerializer(serializers.Serializer):
    """Serializer pour partager un lien de parrainage."""
    
    SHARE_CHANNELS = [
        ('whatsapp', 'WhatsApp'),
        ('telegram', 'Telegram'),
        ('facebook', 'Facebook'),
        ('twitter', 'Twitter'),
        ('instagram', 'Instagram'),
        ('email', 'Email'),
        ('sms', 'SMS'),
        ('copy', 'Copier le lien'),
    ]
    
    channel = serializers.ChoiceField(
        choices=SHARE_CHANNELS,
        help_text=_('Canal de partage')
    )
    
    message = serializers.CharField(
        required=False,
        allow_blank=True,
        help_text=_('Message personnalisé pour le partage')
    )
