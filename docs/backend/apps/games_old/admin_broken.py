# apps/games/admin.py
# ====================

from django.contrib import admin
from django.utils.html import format_html
from django.utils.safestring import mark_safe
from django.urls import reverse
from django.db.models import Count, Sum, Avg
from django.utils.translation import gettext_lazy as _
from django.contrib.admin import SimpleListFilter
from django.utils import timezone
from datetime import timedelta
import json

from .models import (
    GameType, Game, GameInvitation, GameReport,
    Tournament, TournamentParticipant, Leaderboard
)


class GameStatusFilter(SimpleListFilter):
    """Filtre personnalisé pour le statut des jeux."""
    title = _('Statut des parties')
    parameter_name = 'game_status'

    def lookups(self, request, model_admin):
        return (
            ('active', _('Parties actives')),
            ('recent', _('Parties récentes (24h)')),
            ('with_issues', _('Avec problèmes')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'active':
            return queryset.filter(status__in=['waiting', 'ready', 'playing'])
        elif self.value() == 'recent':
            yesterday = timezone.now() - timedelta(days=1)
            return queryset.filter(created_at__gte=yesterday)
        elif self.value() == 'with_issues':
            return queryset.filter(reports__isnull=False).distinct()


class BetAmountFilter(SimpleListFilter):
    """Filtre pour les montants de mise."""
    title = _('Montant de mise')
    parameter_name = 'bet_range'

    def lookups(self, request, model_admin):
        return (
            ('small', _('Petites mises (< 5000)')),
            ('medium', _('Mises moyennes (5000-50000)')),
            ('high', _('Grosses mises (> 50000)')),
        )

    def queryset(self, request, queryset):
        if self.value() == 'small':
            return queryset.filter(bet_amount__lt=5000)
        elif self.value() == 'medium':
            return queryset.filter(bet_amount__gte=5000, bet_amount__lt=50000)
        elif self.value() == 'high':
            return queryset.filter(bet_amount__gte=50000)


@admin.register(GameType)
class GameTypeAdmin(admin.ModelAdmin):
    """Administration des types de jeux."""
    
    list_display = [
        'display_name', 'name', 'category', 'min_players', 'max_players',
        'estimated_duration_display', 'bet_range_display', 'is_active',
        'games_count', 'created_at'
    ]
    list_filter = ['category', 'is_active', 'created_at']
    search_fields = ['name', 'display_name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'games_count', 'total_revenue']
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('name', 'display_name', 'description', 'category')
        }),
        (_('Configuration du jeu'), {
            'fields': ('min_players', 'max_players', 'estimated_duration')
        }),
        (_('Paramètres de mise'), {
            'fields': ('min_bet_fcfa', 'max_bet_fcfa')
        }),
        (_('Média et règles'), {
            'fields': ('icon', 'rules_url')
        }),
        (_('Statut'), {
            'fields': ('is_active',)
        }),
        (_('Statistiques'), {
            'fields': ('games_count', 'total_revenue'),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).annotate(
            game_count=Count('games')
        )
    
    def games_count(self, obj):
        """Nombre de parties créées."""
        return obj.game_count
    games_count.short_description = _('Parties')
    games_count.admin_order_field = 'game_count'
    
    def estimated_duration_display(self, obj):
        """Affichage formaté de la durée."""
        if obj.estimated_duration < 60:
            return f"{obj.estimated_duration} min"
        hours = obj.estimated_duration // 60
        minutes = obj.estimated_duration % 60
        return f"{hours}h{minutes:02d}"
    estimated_duration_display.short_description = _('Durée estimée')
    
    def bet_range_display(self, obj):
        """Affichage de la fourchette de mise."""
        return f"{obj.min_bet_fcfa:,.0f} - {obj.max_bet_fcfa:,.0f} FCFA"
    bet_range_display.short_description = _('Fourchette de mise')
    
    def total_revenue(self, obj):
        """Revenus totaux générés."""
        total = obj.games.filter(status='finished').aggregate(
            total=Sum('commission')
        )['total'] or 0
        return f"{total:,.2f} FCFA"
    total_revenue.short_description = _('Revenus générés')


class GameReportInline(admin.TabularInline):
    """Inline pour les signalements de partie."""
    model = GameReport
    fields = ['reporter', 'reported_user', 'report_type', 'status', 'created_at']
    readonly_fields = ['created_at']
    extra = 0
    max_num = 5


@admin.register(Game)
class GameAdmin(admin.ModelAdmin):
    """Administration des parties."""
    
    list_display = [
        'room_code', 'game_type', 'status_badge', 'players_display',
        'bet_amount_display', 'duration_display', 'created_at'
    ]
    list_filter = [
        GameStatusFilter, 'game_type', 'currency', BetAmountFilter,
        'is_private', 'is_rated', 'created_at'
    ]
    search_fields = ['room_code', 'player1__username', 'player2__username']
    readonly_fields = [
        'id', 'room_code', 'total_pot', 'commission', 'winner_prize',
        'created_at', 'started_at', 'finished_at', 'game_stats'
    ]
    
    fieldsets = (
        (_('Informations de base'), {
            'fields': ('id', 'room_code', 'game_type', 'status')
        }),
        (_('Joueurs'), {
            'fields': ('player1', 'player2', 'current_player', 'winner')
        }),
        (_('Paramètres financiers'), {
            'fields': ('bet_amount', 'currency', 'total_pot', 'commission', 'winner_prize')
        }),
        (_('Paramètres de jeu'), {
            'fields': ('is_private', 'is_rated', 'spectators_allowed')
        }),
        (_('Temps de jeu'), {
            'fields': ('turn_timeout', 'player1_time_left', 'player2_time_left')
        }),
        (_('Données de jeu'), {
            'fields': ('game_data_display', 'move_history_display'),
            'classes': ('collapse',)
        }),
        (_('Statistiques'), {
            'fields': ('game_stats',),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'started_at', 'finished_at', 'last_move_at'),
            'classes': ('collapse',)
        })
    )
    
    inlines = [GameReportInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'game_type', 'player1', 'player2', 'current_player', 'winner'
        ).prefetch_related('reports')
    
    def status_badge(self, obj):
        """Badge coloré pour le statut."""
        colors = {
            'waiting': '#ffc107',      # Jaune
            'ready': '#17a2b8',       # Bleu
            'playing': '#28a745',     # Vert
            'finished': '#6c757d',    # Gris
            'cancelled': '#dc3545',   # Rouge
            'disputed': '#fd7e14',    # Orange
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = _('Statut')


class TournamentParticipantInline(admin.TabularInline):
    """Inline pour les participants au tournoi."""
    model = TournamentParticipant
    fields = ['user', 'seed', 'current_round', 'is_eliminated', 'final_position']
    readonly_fields = ['registered_at']
    extra = 0
    max_num = 20


@admin.register(Tournament)
class TournamentAdmin(admin.ModelAdmin):
    """Administration des tournois."""
    
    list_display = [
        'name', 'game_type', 'tournament_type', 'status_badge',
        'participants_count', 'entry_fee_display', 'start_date'
    ]
    list_filter = [
        'tournament_type', 'status', 'game_type', 'currency', 'start_date'
    ]
    search_fields = ['name', 'description', 'organizer__username']
    readonly_fields = [
        'created_at', 'updated_at', 'participants_count', 'total_entries',
        'prize_distribution'
    ]
    
    fieldsets = (
        (_('Informations générales'), {
            'fields': ('name', 'description', 'game_type', 'tournament_type', 'organizer')
        }),
        (_('Configuration'), {
            'fields': ('max_participants', 'entry_fee', 'currency')
        }),
        (_('Prix'), {
            'fields': ('total_prize_pool', 'winner_prize', 'runner_up_prize', 'prize_distribution')
        }),
        (_('Planning'), {
            'fields': ('registration_start', 'registration_end', 'start_date', 'end_date')
        }),
        (_('Statut'), {
            'fields': ('status',)
        }),
        (_('Statistiques'), {
            'fields': ('participants_count', 'total_entries'),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    inlines = [TournamentParticipantInline]
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'game_type', 'organizer'
        ).annotate(
            participant_count=Count('participants')
        )
    
    def participants_count(self, obj):
        """Nombre de participants."""
        return f"{obj.participant_count}/{obj.max_participants}"
    participants_count.short_description = _('Participants')
    participants_count.admin_order_field = 'participant_count'
    
    def entry_fee_display(self, obj):
        """Affichage des frais d'inscription."""
        if obj.entry_fee > 0:
            return f"{obj.entry_fee:,.0f} {obj.currency}"
        return "Gratuit"
    entry_fee_display.short_description = _('Frais')
    entry_fee_display.admin_order_field = 'entry_fee'
    
    def status_badge(self, obj):
        """Badge coloré pour le statut."""
        colors = {
            'upcoming': '#6c757d',      # Gris
            'registration': '#ffc107',  # Jaune
            'ready': '#17a2b8',        # Bleu
            'ongoing': '#28a745',      # Vert
            'finished': '#6c757d',     # Gris
            'cancelled': '#dc3545',    # Rouge
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = _('Statut')
    
    def total_entries(self, obj):
        """Total des inscriptions."""
        return obj.participants.count() * obj.entry_fee
    total_entries.short_description = _('Total inscriptions')
    
    def prize_distribution(self, obj):
        """Répartition des prix."""
        if obj.total_prize_pool > 0:
            winner_pct = (obj.winner_prize / obj.total_prize_pool) * 100
            runner_pct = (obj.runner_up_prize / obj.total_prize_pool) * 100
            return f"1er: {winner_pct:.1f}%, 2nd: {runner_pct:.1f}%"
        return "-"
    prize_distribution.short_description = _('Répartition')


@admin.register(TournamentParticipant)
class TournamentParticipantAdmin(admin.ModelAdmin):
    """Administration des participants aux tournois."""
    
    list_display = [
        'tournament_name', 'user', 'seed', 'current_round',
        'is_eliminated', 'final_position', 'registered_at'
    ]
    list_filter = ['is_eliminated', 'current_round', 'tournament__status', 'registered_at']
    search_fields = ['tournament__name', 'user__username']
    readonly_fields = ['registered_at']
    
    def tournament_name(self, obj):
        """Nom du tournoi."""
        url = reverse('admin:games_tournament_change', args=[obj.tournament.pk])
        return format_html('<a href="{}">{}</a>', url, obj.tournament.name)
    tournament_name.short_description = _('Tournoi')


@admin.register(Leaderboard)
class LeaderboardAdmin(admin.ModelAdmin):
    """Administration des classements."""
    
    list_display = [
        'rank', 'user', 'leaderboard_type_display', 'game_type',
        'points', 'games_played', 'win_rate_display', 'updated_at'
    ]
    list_filter = [
        'leaderboard_type', 'game_type', 'period_start', 'period_end'
    ]
    search_fields = ['user__username']
    readonly_fields = ['created_at', 'updated_at']
    
    ordering = ['leaderboard_type', 'rank']
    
    def leaderboard_type_display(self, obj):
        """Type de classement avec badge."""
        colors = {
            'global': '#28a745',    # Vert
            'monthly': '#17a2b8',   # Bleu
            'weekly': '#ffc107',    # Jaune
            'game_type': '#6f42c1', # Violet
        }
        color = colors.get(obj.leaderboard_type, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_leaderboard_type_display()
        )
    leaderboard_type_display.short_description = _('Type')
    
    def win_rate_display(self, obj):
        """Taux de victoire formaté."""
        return f"{obj.win_rate:.1f}%"
    win_rate_display.short_description = _('Taux victoire')
    win_rate_display.admin_order_field = 'win_rate'


# Actions globales personnalisées

def export_games_csv(modeladmin, request, queryset):
    """Exporter les parties en CSV."""
    import csv
    from django.http import HttpResponse
    
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="games_export.csv"'
    
    writer = csv.writer(response)
    writer.writerow([
        'Code Partie', 'Type Jeu', 'Joueur 1', 'Joueur 2', 'Statut',
        'Mise', 'Devise', 'Gagnant', 'Date Création', 'Date Début', 'Date Fin'
    ])
    
    for game in queryset:
        writer.writerow([
            game.room_code,
            game.game_type.display_name,
            game.player1.username if game.player1 else '',
            game.player2.username if game.player2 else '',
            game.get_status_display(),
            game.bet_amount,
            game.currency,
            game.winner.username if game.winner else '',
            game.created_at.strftime('%Y-%m-%d %H:%M'),
            game.started_at.strftime('%Y-%m-%d %H:%M') if game.started_at else '',
            game.finished_at.strftime('%Y-%m-%d %H:%M') if game.finished_at else '',
        ])
    
    return response

export_games_csv.short_description = _("Exporter en CSV")


# Configuration avancée de l'admin

class GameAdminConfig(admin.ModelAdmin):
    """Configuration avancée pour l'admin des jeux."""
    
    def get_readonly_fields(self, request, obj=None):
        """Champs en lecture seule selon le contexte."""
        readonly = list(self.readonly_fields)
        
        if obj and obj.status in ['playing', 'finished']:
            # Ne pas permettre de modifier certains champs pour les parties en cours/finies
            readonly.extend(['player1', 'player2', 'bet_amount', 'currency'])
        
        return readonly
    
    def has_delete_permission(self, request, obj=None):
        """Permissions de suppression."""
        if obj and obj.status in ['playing']:
            # Ne pas permettre de supprimer les parties en cours
            return False
        return super().has_delete_permission(request, obj)
    
    def save_model(self, request, obj, form, change):
        """Actions lors de la sauvegarde."""
        if not change:  # Nouvelle création
            obj.created_by_admin = True
        
        super().save_model(request, obj, form, change)
        
        # Log des modifications importantes
        if change and 'status' in form.changed_data:
            from apps.core.utils import log_admin_activity
            log_admin_activity(
                admin_user=request.user,
                action='game_status_changed',
                target=obj,
                details=f"Statut changé vers {obj.status}"
            )


# Widget personnalisé pour JSON
class JSONEditorWidget(admin.widgets.AdminTextareaWidget):
    """Widget personnalisé pour éditer du JSON."""
    
    class Media:
        css = {
            'all': ('admin/css/json-editor.css',)
        }
        js = ('admin/js/json-editor.js',)
    
    def __init__(self, attrs=None):
        default_attrs = {
            'class': 'json-editor',
            'rows': 10,
            'cols': 80
        }
        if attrs:
            default_attrs.update(attrs)
        super().__init__(default_attrs)


# Personnalisation du site admin
admin.site.site_header = "RUMO RUSH - Administration"
admin.site.site_title = "RUMO RUSH Admin"
admin.site.index_title = "Tableau de bord"

# Ajout d'actions globales
admin.site.add_action(export_games_csv, 'export_games_csv')


# Statistiques personnalisées pour le tableau de bord
def get_dashboard_stats():
    """Obtenir les statistiques pour le tableau de bord."""
    from django.db.models import Count, Sum, Avg
    from django.utils import timezone
    from datetime import timedelta
    
    today = timezone.now().date()
    yesterday = today - timedelta(days=1)
    this_week = today - timedelta(days=7)
    
    stats = {
        'games_today': Game.objects.filter(created_at__date=today).count(),
        'games_yesterday': Game.objects.filter(created_at__date=yesterday).count(),
        'games_this_week': Game.objects.filter(created_at__date__gte=this_week).count(),
        'active_games': Game.objects.filter(status__in=['waiting', 'playing']).count(),
        'total_revenue_today': Game.objects.filter(
            finished_at__date=today
        ).aggregate(total=Sum('commission'))['total'] or 0,
        'avg_bet_amount': Game.objects.aggregate(avg=Avg('bet_amount'))['avg'] or 0,
        'top_game_type': Game.objects.values(
            'game_type__display_name'
        ).annotate(
            count=Count('id')
        ).order_by('-count').first(),
    }
    
    return stats


# Fonction pour ajouter des statistiques au contexte de l'admin
def admin_stats_context(request):
    """Ajouter des statistiques au contexte de l'admin."""
    if request.path.startswith('/admin/') and request.user.is_staff:
        return {'dashboard_stats': get_dashboard_stats()}
    return {}


# Enregistrement des vues personnalisées pour les statistiques
from django.urls import path
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render
from django.http import JsonResponse

@staff_member_required
def games_statistics_view(request):
    """Vue des statistiques de jeux."""
    stats = get_dashboard_stats()
    
    # Données pour les graphiques
    chart_data = {
        'games_by_day': list(Game.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=30)
        ).extra(
            select={'day': 'date(created_at)'}
        ).values('day').annotate(count=Count('id')).order_by('day')),
        
        'games_by_type': list(Game.objects.values(
            'game_type__display_name'
        ).annotate(count=Count('id')).order_by('-count')),
        
        'revenue_by_day': list(Game.objects.filter(
            finished_at__gte=timezone.now() - timedelta(days=30)
        ).extra(
            select={'day': 'date(finished_at)'}
        ).values('day').annotate(revenue=Sum('commission')).order_by('day'))
    }
    
    if request.headers.get('Accept') == 'application/json':
        return JsonResponse({
            'stats': stats,
            'charts': chart_data
        })
    
    return render(request, 'admin/games/statistics.html', {
        'stats': stats,
        'chart_data': chart_data
    })

# URLs personnalisées pour l'admin
games_admin_urls = [
    path('statistics/', games_statistics_view, name='games_statistics'),
],
            obj.get_status_display()
        )
    status_badge.short_description = _('Statut')
    
    def players_display(self, obj):
        """Affichage des joueurs."""
        p1 = obj.player1.username if obj.player1 else '?'
        p2 = obj.player2.username if obj.player2 else '?'
        return f"{p1} vs {p2}"
    players_display.short_description = _('Joueurs')
    
    def bet_amount_display(self, obj):
        """Affichage du montant de mise."""
        return f"{obj.bet_amount:,.0f} {obj.currency}"
    bet_amount_display.short_description = _('Mise')
    bet_amount_display.admin_order_field = 'bet_amount'
    
    def duration_display(self, obj):
        """Durée de la partie."""
        if obj.started_at and obj.finished_at:
            duration = obj.finished_at - obj.started_at
            total_seconds = int(duration.total_seconds())
            hours = total_seconds // 3600
            minutes = (total_seconds % 3600) // 60
            if hours > 0:
                return f"{hours}h{minutes:02d}min"
            else:
                return f"{minutes}min"
        elif obj.started_at:
            duration = timezone.now() - obj.started_at
            total_seconds = int(duration.total_seconds())
            minutes = total_seconds // 60
            return f"{minutes}min (en cours)"
        return "-"
    duration_display.short_description = _('Durée')
    
    def game_data_display(self, obj):
        """Affichage formaté des données de jeu."""
        if obj.game_data:
            formatted_data = json.dumps(obj.game_data, indent=2, ensure_ascii=False)
            return format_html('<pre>{}</pre>', formatted_data)
        return "-"
    game_data_display.short_description = _('Données de jeu')
    
    def move_history_display(self, obj):
        """Affichage de l'historique des coups."""
        if obj.move_history:
            moves = obj.move_history[-10:]  # Derniers 10 coups
            moves_text = "\n".join(f"{i+1}. {move}" for i, move in enumerate(moves))
            return format_html('<pre>{}</pre>', moves_text)
        return "-"
    move_history_display.short_description = _('Historique (10 derniers)')
    
    def game_stats(self, obj):
        """Statistiques de la partie."""
        stats = []
        
        # Nombre de coups
        if obj.move_history:
            stats.append(f"Coups joués: {len(obj.move_history)}")
        
        # Temps de jeu
        if obj.started_at:
            if obj.finished_at:
                duration = obj.finished_at - obj.started_at
                stats.append(f"Durée totale: {duration}")
            else:
                stats.append(f"En cours depuis: {timezone.now() - obj.started_at}")
        
        # Revenus générés
        if obj.status == 'finished':
            stats.append(f"Commission: {obj.commission} {obj.currency}")
        
        return "\n".join(stats) if stats else "-"
    game_stats.short_description = _('Statistiques')
    
    actions = ['mark_as_disputed', 'cancel_games', 'export_game_data']
    
    def mark_as_disputed(self, request, queryset):
        """Marquer les parties comme disputées."""
        updated = queryset.update(status='disputed')
        self.message_user(
            request,
            f"{updated} partie(s) marquée(s) comme disputée(s)."
        )
    mark_as_disputed.short_description = _("Marquer comme disputé")
    
    def cancel_games(self, request, queryset):
        """Annuler des parties."""
        count = 0
        for game in queryset.filter(status__in=['waiting', 'ready']):
            game.cancel_game(reason='cancelled_by_admin')
            count += 1
        
        self.message_user(
            request,
            f"{count} partie(s) annulée(s)."
        )
    cancel_games.short_description = _("Annuler les parties")


@admin.register(GameInvitation)
class GameInvitationAdmin(admin.ModelAdmin):
    """Administration des invitations de partie."""
    
    list_display = [
        'game_room_code', 'inviter', 'invitee', 'status_badge',
        'created_at', 'expires_at', 'is_expired'
    ]
    list_filter = ['status', 'created_at', 'expires_at']
    search_fields = [
        'game__room_code', 'inviter__username', 'invitee__username'
    ]
    readonly_fields = ['created_at', 'responded_at', 'is_expired']
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related(
            'game', 'inviter', 'invitee'
        )
    
    def game_room_code(self, obj):
        """Code de la partie."""
        if obj.game:
            url = reverse('admin:games_game_change', args=[obj.game.pk])
            return format_html('<a href="{}">{}</a>', url, obj.game.room_code)
        return "-"
    game_room_code.short_description = _('Code partie')
    
    def status_badge(self, obj):
        """Badge coloré pour le statut."""
        colors = {
            'pending': '#ffc107',     # Jaune
            'accepted': '#28a745',   # Vert
            'declined': '#dc3545',   # Rouge
            'expired': '#6c757d',    # Gris
            'cancelled': '#fd7e14',  # Orange
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = _('Statut')
    
    def is_expired(self, obj):
        """Vérifier si l'invitation a expiré."""
        if obj.expires_at and timezone.now() > obj.expires_at:
            return format_html(
                '<span style="color: red;">Oui</span>'
            )
        return format_html(
            '<span style="color: green;">Non</span>'
        )
    is_expired.short_description = _('Expirée')


@admin.register(GameReport)
class GameReportAdmin(admin.ModelAdmin):
    """Administration des signalements."""
    
    list_display = [
        'id', 'game_room_code', 'reporter', 'reported_user',
        'report_type', 'status_badge', 'created_at'
    ]
    list_filter = ['report_type', 'status', 'created_at']
    search_fields = [
        'game__room_code', 'reporter__username', 'reported_user__username'
    ]
    readonly_fields = ['created_at', 'updated_at']
    
    fieldsets = (
        (_('Signalement'), {
            'fields': ('game', 'reporter', 'reported_user', 'report_type')
        }),
        (_('Description'), {
            'fields': ('description', 'evidence')
        }),
        (_('Traitement'), {
            'fields': ('status', 'admin_notes', 'resolved_by', 'resolved_at')
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def game_room_code(self, obj):
        """Code de la partie."""
        if obj.game:
            url = reverse('admin:games_game_change', args=[obj.game.pk])
            return format_html('<a href="{}">{}</a>', url, obj.game.room_code)
        return "-"
    game_room_code.short_description = _('Code partie')
    
    def status_badge(self, obj):
        """Badge coloré pour le statut."""
        colors = {
            'pending': '#ffc107',      # Jaune
            'under_review': '#17a2b8', # Bleu
            'resolved': '#28a745',     # Vert
            'dismissed': '#6c757d',    # Gris
        }
        color = colors.get(obj.status, '#6c757d')
        return format_html(
            '<span style="color: {}; font-weight: bold;">{}</span>',
            color,
            obj.get_status_display()
        )
    status_badge.short_description = _('Statut')
