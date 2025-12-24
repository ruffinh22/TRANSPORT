from django.contrib import admin
from django.utils.html import format_html
from django.urls import path, reverse
from django.shortcuts import redirect
from django.contrib import messages
from django.db.models import Sum, Count, Q
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from .models import (
    ReferralProgram, Referral, ReferralCommission,
    PremiumSubscription, ReferralStatistics, ReferralBonus
)
from .tasks import recalculate_user_statistics


@admin.register(ReferralProgram)
class ReferralProgramAdmin(admin.ModelAdmin):
    """Administration des programmes de parrainage."""
    
    list_display = [
        'name', 'commission_type', 'commission_rate', 'status',
        'is_default', 'total_referrals', 'total_commissions_paid',
        'created_at'
    ]
    list_filter = ['commission_type', 'status', 'is_default', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        ('Informations générales', {
            'fields': ('name', 'description', 'status', 'is_default')
        }),
        ('Configuration des commissions', {
            'fields': (
                'commission_type', 'commission_rate', 'fixed_commission',
                'min_bet_for_commission', 'free_games_limit'
            )
        }),
        ('Limites', {
            'fields': (
                'max_commission_per_referral', 'max_daily_commission',
                'max_monthly_commission'
            ),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def total_referrals(self, obj):
        """Nombre total de parrainages actifs."""
        count = obj.referrals.filter(status='active').count()
        return format_html(
            '<span style="color: green; font-weight: bold">{}</span>',
            count
        )
    total_referrals.short_description = 'Parrainages actifs'
    
    def total_commissions_paid(self, obj):
        """Total des commissions payées."""
        total = obj.referrals.aggregate(
            total=Sum('commissions__amount', filter=Q(commissions__status='completed'))
        )['total'] or Decimal('0.00')
        return format_html(
            '<span style="color: blue">{:.2f} FCFA</span>',
            total
        )
    total_commissions_paid.short_description = 'Commissions payées'


@admin.register(Referral)
class ReferralAdmin(admin.ModelAdmin):
    """Administration des parrainages."""
    
    list_display = [
        'referrer_link', 'referred_link', 'program', 'status',
        'total_commission_earned', 'is_premium_referrer', 'created_at'
    ]
    list_filter = [
        'status', 'is_premium_referrer', 'program', 'created_at'
    ]
    search_fields = [
        'referrer__username', 'referrer__email',
        'referred__username', 'referred__email'
    ]
    readonly_fields = [
        'total_commission_earned', 'created_at', 'updated_at'
    ]
    
    fieldsets = (
        ('Relation de parrainage', {
            'fields': ('referrer', 'referred', 'program', 'status')
        }),
        ('Statistiques', {
            'fields': (
                'total_commission_earned', 'is_premium_referrer'
            ),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['suspend_referrals', 'reactivate_referrals', 'recalculate_statistics']
    
    def referrer_link(self, obj):
        """Lien vers le profil du parrain."""
        url = reverse('admin:auth_user_change', args=[obj.referrer.pk])
        return format_html(
            '<a href="{}">{}</a>',
            url, obj.referrer.username
        )
    referrer_link.short_description = 'Parrain'
    
    def referred_link(self, obj):
        """Lien vers le profil du filleul."""
        url = reverse('admin:auth_user_change', args=[obj.referred.pk])
        return format_html(
            '<a href="{}">{}</a>',
            url, obj.referred.username
        )
    referred_link.short_description = 'Filleul'
    
    def suspend_referrals(self, request, queryset):
        """Action pour suspendre des parrainages."""
        updated = queryset.filter(status='active').update(status='suspended')
        self.message_user(
            request,
            f'{updated} parrainage(s) suspendu(s).',
            messages.SUCCESS
        )
    suspend_referrals.short_description = "Suspendre les parrainages sélectionnés"
    
    def reactivate_referrals(self, request, queryset):
        """Action pour réactiver des parrainages."""
        updated = queryset.filter(status='suspended').update(status='active')
        self.message_user(
            request,
            f'{updated} parrainage(s) réactivé(s).',
            messages.SUCCESS
        )
    reactivate_referrals.short_description = "Réactiver les parrainages sélectionnés"
    
    def recalculate_statistics(self, request, queryset):
        """Action pour recalculer les statistiques."""
        user_ids = queryset.values_list('referrer', flat=True).distinct()
        
        for user_id in user_ids:
            recalculate_user_statistics.delay(str(user_id))
        
        self.message_user(
            request,
            f'Recalcul des statistiques lancé pour {len(user_ids)} utilisateur(s).',
            messages.SUCCESS
        )
    recalculate_statistics.short_description = "Recalculer les statistiques"


@admin.register(ReferralCommission)
class ReferralCommissionAdmin(admin.ModelAdmin):
    """Administration des commissions."""
    
    list_display = [
        'commission_id', 'referrer_username', 'referred_username',
        'amount_display', 'status', 'game_link', 'created_at'
    ]
    list_filter = [
        'status', 'currency', 'created_at', 'processed_at'
    ]
    search_fields = [
        'referral__referrer__username',
        'referral__referred__username',
        'game__id'
    ]
    readonly_fields = [
        'referrer_balance_before', 'referrer_balance_after',
        'created_at', 'processed_at'
    ]
    
    fieldsets = (
        ('Commission', {
            'fields': ('referral', 'game', 'amount', 'currency', 'status')
        }),
        ('Transaction', {
            'fields': ('transaction', 'failure_reason'),
            'classes': ('collapse',)
        }),
        ('Soldes', {
            'fields': ('referrer_balance_before', 'referrer_balance_after'),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'processed_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['process_pending_commissions', 'cancel_commissions']
    
    def commission_id(self, obj):
        """ID raccourci de la commission."""
        return str(obj.id)[:8]
    commission_id.short_description = 'ID'
    
    def referrer_username(self, obj):
        """Nom d'utilisateur du parrain."""
        return obj.referral.referrer.username
    referrer_username.short_description = 'Parrain'
    
    def referred_username(self, obj):
        """Nom d'utilisateur du filleul."""
        return obj.referral.referred.username
    referred_username.short_description = 'Filleul'
    
    def amount_display(self, obj):
        """Affichage formaté du montant."""
        color = 'green' if obj.status == 'completed' else 'orange'
        return format_html(
            '<span style="color: {}; font-weight: bold">{:.2f} {}</span>',
            color, obj.amount, obj.currency
        )
    amount_display.short_description = 'Montant'
    
    def game_link(self, obj):
        """Lien vers le jeu."""
        if obj.game:
            return format_html(
                '<a href="/admin/games/game/{}/change/">{}</a>',
                obj.game.pk, str(obj.game.id)[:8]
            )
        return '-'
    game_link.short_description = 'Jeu'
    
    def process_pending_commissions(self, request, queryset):
        """Traiter les commissions en attente."""
        pending = queryset.filter(status='pending')
        
        for commission in pending:
            try:
                commission.process_commission()
                messages.success(request, f'Commission {commission.id} traitée.')
            except Exception as e:
                messages.error(request, f'Erreur commission {commission.id}: {e}')
    
    process_pending_commissions.short_description = "Traiter les commissions sélectionnées"
    
    def cancel_commissions(self, request, queryset):
        """Annuler des commissions."""
        updated = queryset.filter(status='pending').update(
            status='cancelled',
            failure_reason='Annulé par administrateur'
        )
        self.message_user(
            request,
            f'{updated} commission(s) annulée(s).',
            messages.SUCCESS
        )
    cancel_commissions.short_description = "Annuler les commissions sélectionnées"


@admin.register(PremiumSubscription)
class PremiumSubscriptionAdmin(admin.ModelAdmin):
    """Administration des abonnements premium."""
    
    list_display = [
        'user_link', 'plan_type', 'price_display', 'status',
        'start_date', 'end_date', 'auto_renewal', 'is_active_display'
    ]
    list_filter = [
        'plan_type', 'status', 'auto_renewal', 'currency',
        'start_date', 'end_date'
    ]
    search_fields = ['user__username', 'user__email']
    readonly_fields = [
        'created_at', 'updated_at', 'cancelled_at'
    ]
    
    fieldsets = (
        ('Abonnement', {
            'fields': ('user', 'plan_type', 'price', 'currency', 'status')
        }),
        ('Période', {
            'fields': ('start_date', 'end_date', 'auto_renewal')
        }),
        ('Transaction', {
            'fields': ('transaction',),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at', 'cancelled_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['cancel_subscriptions', 'renew_subscriptions']
    
    def user_link(self, obj):
        """Lien vers l'utilisateur."""
        url = reverse('admin:auth_user_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'Utilisateur'
    
    def price_display(self, obj):
        """Affichage formaté du prix."""
        return format_html(
            '<span style="font-weight: bold">{:.2f} {}</span>',
            obj.price, obj.currency
        )
    price_display.short_description = 'Prix'
    
    def is_active_display(self, obj):
        """Indicateur d'activité."""
        if obj.is_active():
            return format_html(
                '<span style="color: green; font-weight: bold">✓ Actif</span>'
            )
        else:
            return format_html(
                '<span style="color: red;">✗ Inactif</span>'
            )
    is_active_display.short_description = 'Statut'
    
    def cancel_subscriptions(self, request, queryset):
        """Annuler des abonnements."""
        for subscription in queryset.filter(status='active'):
            try:
                subscription.cancel('Annulé par administrateur')
                messages.success(request, f'Abonnement {subscription.id} annulé.')
            except Exception as e:
                messages.error(request, f'Erreur {subscription.id}: {e}')
    
    cancel_subscriptions.short_description = "Annuler les abonnements sélectionnés"


@admin.register(ReferralBonus)
class ReferralBonusAdmin(admin.ModelAdmin):
    """Administration des bonus de parrainage."""
    
    list_display = [
        'bonus_type', 'referrer_username', 'amount_display',
        'status', 'expires_at', 'created_at'
    ]
    list_filter = [
        'bonus_type', 'status', 'currency', 'created_at', 'expires_at'
    ]
    search_fields = [
        'referral__referrer__username',
        'description'
    ]
    readonly_fields = ['claimed_at', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Bonus', {
            'fields': (
                'referral', 'bonus_type', 'amount', 'currency',
                'status', 'description'
            )
        }),
        ('Conditions', {
            'fields': (
                'minimum_bet_requirement', 'wagering_requirement',
                'expires_at'
            ),
            'classes': ('collapse',)
        }),
        ('Transaction', {
            'fields': ('transaction',),
            'classes': ('collapse',)
        }),
        ('Métadonnées', {
            'fields': ('created_at', 'updated_at', 'claimed_at'),
            'classes': ('collapse',)
        })
    )
    
    actions = ['approve_bonuses', 'expire_bonuses']
    
    def referrer_username(self, obj):
        """Nom du parrain."""
        return obj.referral.referrer.username
    referrer_username.short_description = 'Parrain'
    
    def amount_display(self, obj):
        """Affichage formaté du montant."""
        color_map = {
            'pending': 'orange',
            'approved': 'green',
            'claimed': 'blue',
            'expired': 'red',
            'cancelled': 'gray'
        }
        color = color_map.get(obj.status, 'black')
        
        return format_html(
            '<span style="color: {}; font-weight: bold">{:.2f} {}</span>',
            color, obj.amount, obj.currency
        )
    amount_display.short_description = 'Montant'
    
    def approve_bonuses(self, request, queryset):
        """Approuver des bonus."""
        updated = queryset.filter(status='pending').update(status='approved')
        self.message_user(
            request,
            f'{updated} bonus approuvé(s).',
            messages.SUCCESS
        )
    approve_bonuses.short_description = "Approuver les bonus sélectionnés"
    
    def expire_bonuses(self, request, queryset):
        """Faire expirer des bonus."""
        updated = queryset.filter(
            status__in=['pending', 'approved']
        ).update(status='expired')
        
        self.message_user(
            request,
            f'{updated} bonus expiré(s).',
            messages.SUCCESS
        )
    expire_bonuses.short_description = "Faire expirer les bonus sélectionnés"


@admin.register(ReferralStatistics)
class ReferralStatisticsAdmin(admin.ModelAdmin):
    """Administration des statistiques."""
    
    list_display = [
        'user_link', 'period_type', 'period_start', 'period_end',
        'total_referrals', 'total_commission_earned', 'conversion_rate'
    ]
    list_filter = [
        'period_type', 'period_start', 'period_end'
    ]
    search_fields = ['user__username']
    readonly_fields = [
        'total_referrals', 'active_referrals', 'new_referrals',
        'total_games_played', 'commission_games', 'total_commission_earned',
        'total_bet_volume', 'average_commission_per_game',
        'created_at', 'updated_at'
    ]
    
    def user_link(self, obj):
        """Lien vers l'utilisateur."""
        url = reverse('admin:auth_user_change', args=[obj.user.pk])
        return format_html('<a href="{}">{}</a>', url, obj.user.username)
    user_link.short_description = 'Utilisateur'
    
    def conversion_rate(self, obj):
        """Taux de conversion."""
        if obj.total_referrals > 0:
            rate = (obj.active_referrals / obj.total_referrals) * 100
            return format_html(
                '<span style="font-weight: bold">{:.1f}%</span>',
                rate
            )
        return '0%'
    conversion_rate.short_description = 'Taux conversion'


# Configuration globale de l'admin
admin.site.site_header = "RUMO RUSH - Administration"
admin.site.site_title = "RUMO RUSH Admin"
admin.site.index_title = "Tableau de bord administrateur"
