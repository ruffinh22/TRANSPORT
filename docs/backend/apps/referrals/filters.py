# apps/referrals/filters.py
# ===========================

import django_filters
from django.db.models import Q
from django_filters import rest_framework as filters
from .models import (
    Referral, ReferralCommission, ReferralStatistics, 
    ReferralBonus, PremiumSubscription
)


class ReferralFilter(filters.FilterSet):
    """Filtres pour les parrainages."""
    
    # Filtre par statut
    status = filters.MultipleChoiceFilter(
        choices=Referral.STATUS_CHOICES,
        field_name='status'
    )
    
    # Filtre par période de création
    created_after = filters.DateTimeFilter(field_name='created_at', lookup_expr='gte')
    created_before = filters.DateTimeFilter(field_name='created_at', lookup_expr='lte')
    
    # Filtre par commission minimum gagnée
    min_commission = filters.NumberFilter(field_name='total_commission_earned', lookup_expr='gte')
    max_commission = filters.NumberFilter(field_name='total_commission_earned', lookup_expr='lte')
    
    # Filtre par nombre de parties
    min_games = filters.NumberFilter(field_name='games_played', lookup_expr='gte')
    max_games = filters.NumberFilter(field_name='games_played', lookup_expr='lte')
    
    # Filtre par statut premium du parrain
    is_premium = filters.BooleanFilter(field_name='is_premium_referrer')
    
    # Filtre par nom du filleul
    referred_username = filters.CharFilter(
        field_name='referred__username', 
        lookup_expr='icontains'
    )
    
    # Filtre par activité récente
    has_recent_activity = filters.BooleanFilter(method='filter_recent_activity')
    
    class Meta:
        model = Referral
        fields = [
            'status', 'is_premium_referrer', 'created_after', 'created_before',
            'min_commission', 'max_commission', 'min_games', 'max_games',
            'referred_username', 'has_recent_activity'
        ]
    
    def filter_recent_activity(self, queryset, name, value):
        """Filtrer par activité récente (30 derniers jours)."""
        from django.utils import timezone
        from datetime import timedelta
        
        if value:
            recent_date = timezone.now() - timedelta(days=30)
            return queryset.filter(
                Q(last_commission_date__gte=recent_date) |
                Q(commissions__created_at__gte=recent_date)
            ).distinct()
        return queryset


class CommissionFilter(filters.FilterSet):
    """Filtres pour les commissions de parrainage."""
    
    # Filtre par statut
    status = filters.MultipleChoiceFilter(
        choices=ReferralCommission.STATUS_CHOICES,
        field_name='status'
    )
    
    # Filtre par période
    date_from = filters.DateFilter(field_name='created_at__date', lookup_expr='gte')
    date_to = filters.DateFilter(field_name='created_at__date', lookup_expr='lte')
    
    # Filtre par montant
    amount_min = filters.NumberFilter(field_name='amount', lookup_expr='gte')
    amount_max = filters.NumberFilter(field_name='amount', lookup_expr='lte')
    
    # Filtre par devise
    currency = filters.ChoiceFilter(
        choices=[('FCFA', 'FCFA'), ('EUR', 'EUR'), ('USD', 'USD')]
    )
    
    # Filtre par type de jeu
    game_type = filters.CharFilter(field_name='game__game_type')
    
    # Filtre par nom du filleul
    referred_user = filters.CharFilter(
        field_name='referral__referred__username',
        lookup_expr='icontains'
    )
    
    class Meta:
        model = ReferralCommission
        fields = [
            'status', 'currency', 'date_from', 'date_to',
            'amount_min', 'amount_max', 'game_type', 'referred_user'
        ]


class StatisticsFilter(filters.FilterSet):
    """Filtres pour les statistiques de parrainage."""
    
    # Filtre par type de période
    period_type = filters.ChoiceFilter(choices=ReferralStatistics.PERIOD_TYPES)
    
    # Filtre par période
    period_start = filters.DateFilter(field_name='period_start', lookup_expr='gte')
    period_end = filters.DateFilter(field_name='period_end', lookup_expr='lte')
    
    # Filtre par performance
    min_commission = filters.NumberFilter(field_name='total_commission_earned', lookup_expr='gte')
    min_referrals = filters.NumberFilter(field_name='total_referrals', lookup_expr='gte')
    
    class Meta:
        model = ReferralStatistics
        fields = ['period_type', 'period_start', 'period_end', 'min_commission', 'min_referrals']


class BonusFilter(filters.FilterSet):
    """Filtres pour les bonus de parrainage."""
    
    # Filtre par type de bonus
    bonus_type = filters.ChoiceFilter(choices=ReferralBonus.BONUS_TYPES)
    
    # Filtre par statut
    status = filters.MultipleChoiceFilter(choices=ReferralBonus.STATUS_CHOICES)
    
    # Filtre par disponibilité
    available_only = filters.BooleanFilter(method='filter_available_only')
    
    # Filtre par montant
    amount_min = filters.NumberFilter(field_name='amount', lookup_expr='gte')
    amount_max = filters.NumberFilter(field_name='amount', lookup_expr='lte')
    
    class Meta:
        model = ReferralBonus
        fields = ['bonus_type', 'status', 'amount_min', 'amount_max', 'available_only']
    
    def filter_available_only(self, queryset, name, value):
        """Filtrer seulement les bonus réclamables."""
        if value:
            from django.utils import timezone
            return queryset.filter(
                status='approved',
                expires_at__gt=timezone.now()
            )
        return queryset


class SubscriptionFilter(filters.FilterSet):
    """Filtres pour les abonnements premium."""
    
    # Filtre par type de plan
    plan_type = filters.ChoiceFilter(choices=PremiumSubscription.PLAN_TYPES)
    
    # Filtre par statut
    status = filters.MultipleChoiceFilter(choices=PremiumSubscription.STATUS_CHOICES)
    
    # Filtre par renouvellement automatique
    auto_renewal = filters.BooleanFilter()
    
    # Filtre par période
    start_date_after = filters.DateTimeFilter(field_name='start_date', lookup_expr='gte')
    end_date_before = filters.DateTimeFilter(field_name='end_date', lookup_expr='lte')
    
    # Filtrer seulement les abonnements actifs
    active_only = filters.BooleanFilter(method='filter_active_only')
    
    class Meta:
        model = PremiumSubscription
        fields = [
            'plan_type', 'status', 'auto_renewal', 
            'start_date_after', 'end_date_before', 'active_only'
        ]
    
    def filter_active_only(self, queryset, name, value):
        """Filtrer seulement les abonnements actifs."""
        if value:
            from django.utils import timezone
            return queryset.filter(
                status='active',
                start_date__lte=timezone.now()
            ).filter(
                Q(end_date__isnull=True) | Q(end_date__gt=timezone.now())
            )
        return queryset
