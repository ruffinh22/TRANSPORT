# apps/games/tasks.py
# ===================

from celery import shared_task
from django.utils import timezone
from django.db.models import Q, Count, Sum, Avg
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from datetime import timedelta
import logging
from typing import List, Dict, Optional

from .models import Game, GameType, Tournament, Leaderboard, GameInvitation
from apps.accounts.models import User
from apps.core.utils import log_user_activity

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def check_game_timeouts(self):
    """Vérifier et gérer les timeouts des parties."""
    try:
        # Trouver les parties avec timeout
        timeout_threshold = timezone.now() - timedelta(seconds=120)  # 2 minutes
        
        timed_out_games = Game.objects.filter(
            status='playing',
            turn_start_time__lt=timeout_threshold
        ).select_related('current_player', 'player1', 'player2')
        
        processed_count = 0
        
        for game in timed_out_games:
            try:
                # Déterminer le gagnant (l'adversaire du joueur qui a timeout)
                if game.current_player == game.player1:
                    winner = game.player2
                    loser = game.player1
                else:
                    winner = game.player1
                    loser = game.player2
                
                # Terminer la partie
                game.end_game(winner, reason='timeout')
                
                # Log de l'activité
                log_user_activity(
                    user=loser,
                    activity_type='game_lost_timeout',
                    description=f'Partie perdue par timeout: {game.room_code}',
                    metadata={'game_id': str(game.id), 'opponent': winner.username}
                )
                
                log_user_activity(
                    user=winner,
                    activity_type='game_won_timeout',
                    description=f'Partie gagnée par timeout: {game.room_code}',
                    metadata={'game_id': str(game.id), 'opponent': loser.username}
                )
                
                processed_count += 1
                
                # Envoyer notification par WebSocket si possible
                send_timeout_notification.delay(str(game.id), winner.id, loser.id)
                
            except Exception as e:
                logger.error(f"Erreur lors du traitement du timeout pour la partie {game.id}: {e}")
        
        logger.info(f"Traité {processed_count} timeouts de partie")
        return {'processed': processed_count}
        
    except Exception as exc:
        logger.error(f"Erreur lors de la vérification des timeouts: {exc}")
        self.retry(countdown=60, exc=exc)


@shared_task(bind=True, max_retries=3)
def cleanup_expired_invitations(self):
    """Nettoyer les invitations expirées."""
    try:
        expired_invitations = GameInvitation.objects.filter(
            status='pending',
            expires_at__lt=timezone.now()
        )
        
        count = expired_invitations.count()
        expired_invitations.update(status='expired')
        
        logger.info(f"Nettoyé {count} invitations expirées")
        return {'cleaned': count}
        
    except Exception as exc:
        logger.error(f"Erreur lors du nettoyage des invitations: {exc}")
        self.retry(countdown=300, exc=exc)


@shared_task(bind=True, max_retries=3)
def cleanup_abandoned_games(self):
    """Nettoyer les parties abandonnées."""
    try:
        # Parties en attente depuis plus de 1 heure
        abandoned_threshold = timezone.now() - timedelta(hours=1)
        
        abandoned_games = Game.objects.filter(
            status='waiting',
            created_at__lt=abandoned_threshold,
            player2__isnull=True
        )
        
        processed_count = 0
        
        for game in abandoned_games:
            try:
                game.cancel_game(reason='abandoned')
                processed_count += 1
                
                # Log de l'activité
                if game.player1:
                    log_user_activity(
                        user=game.player1,
                        activity_type='game_abandoned',
                        description=f'Partie abandonnée automatiquement: {game.room_code}',
                        metadata={'game_id': str(game.id)}
                    )
                
            except Exception as e:
                logger.error(f"Erreur lors de la suppression de la partie abandonnée {game.id}: {e}")
        
        logger.info(f"Nettoyé {processed_count} parties abandonnées")
        return {'cleaned': processed_count}
        
    except Exception as exc:
        logger.error(f"Erreur lors du nettoyage des parties abandonnées: {exc}")
        self.retry(countdown=300, exc=exc)


@shared_task(bind=True, max_retries=3)
def update_leaderboards(self):
    """Mettre à jour les classements."""
    try:
        current_date = timezone.now().date()
        
        # Classement global
        update_global_leaderboard.delay()
        
        # Classement mensuel
        if current_date.day == 1:  # Premier du mois
            update_monthly_leaderboard.delay()
        
        # Classement hebdomadaire
        if current_date.weekday() == 0:  # Lundi
            update_weekly_leaderboard.delay()
        
        # Classements par type de jeu
        for game_type in GameType.objects.filter(is_active=True):
            update_game_type_leaderboard.delay(str(game_type.id))
        
        return {'status': 'leaderboard_updates_scheduled'}
        
    except Exception as exc:
        logger.error(f"Erreur lors de la programmation des mises à jour de classements: {exc}")
        self.retry(countdown=300, exc=exc)


@shared_task(bind=True, max_retries=3)
def update_global_leaderboard(self):
    """Mettre à jour le classement global."""
    try:
        # Supprimer l'ancien classement global
        Leaderboard.objects.filter(leaderboard_type='global').delete()
        
        # Calculer les statistiques pour tous les utilisateurs ayant joué
        users_stats = User.objects.filter(
            Q(games_as_player1__status='finished') | 
            Q(games_as_player2__status='finished')
        ).annotate(
            total_games=Count('games_as_player1', filter=Q(games_as_player1__status='finished')) +
                       Count('games_as_player2', filter=Q(games_as_player2__status='finished')),
            total_wins=Count('won_games'),
            total_winnings=Sum('won_games__winner_prize') or 0
        ).filter(total_games__gt=0).order_by('-total_wins', '-total_winnings')
        
        # Créer les entrées de classement
        rank = 1
        for user in users_stats:
            win_rate = (user.total_wins / user.total_games) * 100 if user.total_games > 0 else 0
            points = user.total_wins * 10 + int(win_rate)  # Système de points simple
            
            Leaderboard.objects.create(
                user=user,
                leaderboard_type='global',
                rank=rank,
                points=points,
                games_played=user.total_games,
                games_won=user.total_wins,
                win_rate=win_rate,
                total_winnings=user.total_winnings,
                period_start=timezone.now().date() - timedelta(days=365),
                period_end=timezone.now().date()
            )
            rank += 1
            
            # Limiter le classement aux 1000 premiers
            if rank > 1000:
                break
        
        logger.info(f"Mis à jour le classement global avec {rank-1} entrées")
        return {'updated': rank-1}
        
    except Exception as exc:
        logger.error(f"Erreur lors de la mise à jour du classement global: {exc}")
        self.retry(countdown=300, exc=exc)


@shared_task(bind=True, max_retries=3)
def update_monthly_leaderboard(self):
    """Mettre à jour le classement mensuel."""
    try:
        current_date = timezone.now().date()
        start_of_month = current_date.replace(day=1)
        
        # Supprimer l'ancien classement mensuel
        Leaderboard.objects.filter(
            leaderboard_type='monthly',
            period_start=start_of_month
        ).delete()
        
        # Calculer les statistiques du mois
        users_stats = User.objects.filter(
            Q(games_as_player1__status='finished', games_as_player1__finished_at__date__gte=start_of_month) |
            Q(games_as_player2__status='finished', games_as_player2__finished_at__date__gte=start_of_month)
        ).annotate(
            monthly_games=Count('games_as_player1', filter=Q(
                games_as_player1__status='finished',
                games_as_player1__finished_at__date__gte=start_of_month
            )) + Count('games_as_player2', filter=Q(
                games_as_player2__status='finished',
                games_as_player2__finished_at__date__gte=start_of_month
            )),
            monthly_wins=Count('won_games', filter=Q(won_games__finished_at__date__gte=start_of_month)),
            monthly_winnings=Sum('won_games__winner_prize', filter=Q(
                won_games__finished_at__date__gte=start_of_month
            )) or 0
        ).filter(monthly_games__gt=0).order_by('-monthly_wins', '-monthly_winnings')
        
        # Créer les entrées de classement mensuel
        rank = 1
        for user in users_stats:
            win_rate = (user.monthly_wins / user.monthly_games) * 100 if user.monthly_games > 0 else 0
            points = user.monthly_wins * 10 + int(win_rate)
            
            Leaderboard.objects.create(
                user=user,
                leaderboard_type='monthly',
                rank=rank,
                points=points,
                games_played=user.monthly_games,
                games_won=user.monthly_wins,
                win_rate=win_rate,
                total_winnings=user.monthly_winnings,
                period_start=start_of_month,
                period_end=current_date
            )
            rank += 1
            
            if rank > 100:  # Top 100 mensuel
                break
        
        logger.info(f"Mis à jour le classement mensuel avec {rank-1} entrées")
        return {'updated': rank-1}
        
    except Exception as exc:
        logger.error(f"Erreur lors de la mise à jour du classement mensuel: {exc}")
        self.retry(countdown=300, exc=exc)


@shared_task(bind=True, max_retries=3)
def update_weekly_leaderboard(self):
    """Mettre à jour le classement hebdomadaire."""
    try:
        current_date = timezone.now().date()
        start_of_week = current_date - timedelta(days=current_date.weekday())
        
        # Supprimer l'ancien classement hebdomadaire
        Leaderboard.objects.filter(
            leaderboard_type='weekly',
            period_start=start_of_week
        ).delete()
        
        # Calculer les statistiques de la semaine
        users_stats = User.objects.filter(
            Q(games_as_player1__status='finished', games_as_player1__finished_at__date__gte=start_of_week) |
            Q(games_as_player2__status='finished', games_as_player2__finished_at__date__gte=start_of_week)
        ).annotate(
            weekly_games=Count('games_as_player1', filter=Q(
                games_as_player1__status='finished',
                games_as_player1__finished_at__date__gte=start_of_week
            )) + Count('games_as_player2', filter=Q(
                games_as_player2__status='finished',
                games_as_player2__finished_at__date__gte=start_of_week
            )),
            weekly_wins=Count('won_games', filter=Q(won_games__finished_at__date__gte=start_of_week)),
            weekly_winnings=Sum('won_games__winner_prize', filter=Q(
                won_games__finished_at__date__gte=start_of_week
            )) or 0
        ).filter(weekly_games__gt=0).order_by('-weekly_wins', '-weekly_winnings')
        
        # Créer les entrées de classement hebdomadaire
        rank = 1
        for user in users_stats:
            win_rate = (user.weekly_wins / user.weekly_games) * 100 if user.weekly_games > 0 else 0
            points = user.weekly_wins * 10 + int(win_rate)
            
            Leaderboard.objects.create(
                user=user,
                leaderboard_type='weekly',
                rank=rank,
                points=points,
                games_played=user.weekly_games,
                games_won=user.weekly_wins,
                win_rate=win_rate,
                total_winnings=user.weekly_winnings,
                period_start=start_of_week,
                period_end=current_date
            )
            rank += 1
            
            if rank > 50:  # Top 50 hebdomadaire
                break
        
        logger.info(f"Mis à jour le classement hebdomadaire avec {rank-1} entrées")
        return {'updated': rank-1}
        
    except Exception as exc:
        logger.error(f"Erreur lors de la mise à jour du classement hebdomadaire: {exc}")
        self.retry(countdown=300, exc=exc)


@shared_task(bind=True, max_retries=3)
def update_game_type_leaderboard(self, game_type_id: str):
    """Mettre à jour le classement pour un type de jeu spécifique."""
    try:
        game_type = GameType.objects.get(id=game_type_id)
        
        # Supprimer l'ancien classement pour ce type de jeu
        Leaderboard.objects.filter(
            leaderboard_type='game_type',
            game_type=game_type
        ).delete()
        
        # Calculer les statistiques pour ce type de jeu
        users_stats = User.objects.filter(
            Q(games_as_player1__game_type=game_type, games_as_player1__status='finished') |
            Q(games_as_player2__game_type=game_type, games_as_player2__status='finished')
        ).annotate(
            type_games=Count('games_as_player1', filter=Q(
                games_as_player1__game_type=game_type,
                games_as_player1__status='finished'
            )) + Count('games_as_player2', filter=Q(
                games_as_player2__game_type=game_type,
                games_as_player2__status='finished'
            )),
            type_wins=Count('won_games', filter=Q(
                won_games__game_type=game_type
            )),
            type_winnings=Sum('won_games__winner_prize', filter=Q(
                won_games__game_type=game_type
            )) or 0
        ).filter(type_games__gt=0).order_by('-type_wins', '-type_winnings')
        
        # Créer les entrées de classement par type
        rank = 1
        for user in users_stats:
            win_rate = (user.type_wins / user.type_games) * 100 if user.type_games > 0 else 0
            points = user.type_wins * 10 + int(win_rate)
            
            Leaderboard.objects.create(
                user=user,
                leaderboard_type='game_type',
                game_type=game_type,
                rank=rank,
                points=points,
                games_played=user.type_games,
                games_won=user.type_wins,
                win_rate=win_rate,
                total_winnings=user.type_winnings,
                period_start=timezone.now().date() - timedelta(days=365),
                period_end=timezone.now().date()
            )
            rank += 1
            
            if rank > 100:  # Top 100 par type
                break
        
        logger.info(f"Mis à jour le classement {game_type.display_name} avec {rank-1} entrées")
        return {'game_type': game_type.display_name, 'updated': rank-1}
        
    except GameType.DoesNotExist:
        logger.error(f"Type de jeu non trouvé: {game_type_id}")
        return {'error': 'game_type_not_found'}
    except Exception as exc:
        logger.error(f"Erreur lors de la mise à jour du classement par type: {exc}")
        self.retry(countdown=300, exc=exc)


@shared_task(bind=True, max_retries=3)
def send_timeout_notification(self, game_id: str, winner_id: int, loser_id: int):
    """Envoyer une notification de timeout."""
    try:
        game = Game.objects.get(id=game_id)
        winner = User.objects.get(id=winner_id)
        loser = User.objects.get(id=loser_id)
        
        # Envoyer notification par WebSocket via channels
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        channel_layer = get_channel_layer()
        
        # Notification au gagnant
        async_to_sync(channel_layer.group_send)(
            f"user_{winner.id}",
            {
                'type': 'game_notification',
                'message': f'Vous avez gagné la partie {game.room_code} par timeout de votre adversaire',
                'game_id': str(game.id),
                'notification_type': 'game_won_timeout'
            }
        )
        
        # Notification au perdant
        async_to_sync(channel_layer.group_send)(
            f"user_{loser.id}",
            {
                'type': 'game_notification',
                'message': f'Vous avez perdu la partie {game.room_code} par timeout',
                'game_id': str(game.id),
                'notification_type': 'game_lost_timeout'
            }
        )
        
        logger.info(f"Notifications de timeout envoyées pour la partie {game.room_code}")
        return {'notifications_sent': 2}
        
    except (Game.DoesNotExist, User.DoesNotExist) as e:
        logger.error(f"Erreur lors de l'envoi de notification de timeout: {e}")
        return {'error': str(e)}
    except Exception as exc:
        logger.error(f"Erreur lors de l'envoi de notification de timeout: {exc}")
        self.retry(countdown=60, exc=exc)


@shared_task(bind=True, max_retries=3)
def send_daily_game_report(self):
    """Envoyer le rapport quotidien des jeux."""
    try:
        yesterday = timezone.now().date() - timedelta(days=1)
        
        # Statistiques du jour
        daily_stats = {
            'games_created': Game.objects.filter(created_at__date=yesterday).count(),
            'games_finished': Game.objects.filter(finished_at__date=yesterday).count(),
            'total_revenue': Game.objects.filter(
                finished_at__date=yesterday
            ).aggregate(total=Sum('commission'))['total'] or 0,
            'unique_players': User.objects.filter(
                Q(games_as_player1__created_at__date=yesterday) |
                Q(games_as_player2__created_at__date=yesterday)
            ).count(),
            'most_popular_game': Game.objects.filter(
                created_at__date=yesterday
            ).values('game_type__display_name').annotate(
                count=Count('id')
            ).order_by('-count').first(),
        }
        
        # Préparer l'email
        subject = f'RUMO RUSH - Rapport quotidien du {yesterday.strftime("%d/%m/%Y")}'
        
        html_content = render_to_string('games/emails/daily_report.html', {
            'date': yesterday,
            'stats': daily_stats
        })
        
        # Envoyer aux administrateurs
        admin_emails = User.objects.filter(is_staff=True).values_list('email', flat=True)
        
        for email in admin_emails:
            send_mail(
                subject=subject,
                message='',  # Version texte
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                html_message=html_content,
                fail_silently=False
            )
        
        logger.info(f"Rapport quotidien envoyé à {len(admin_emails)} administrateurs")
        return {'report_sent': len(admin_emails), 'stats': daily_stats}
        
    except Exception as exc:
        logger.error(f"Erreur lors de l'envoi du rapport quotidien: {exc}")
        self.retry(countdown=300, exc=exc)


@shared_task(bind=True, max_retries=3)
def process_tournament_matches(self, tournament_id: str):
    """Traiter les matchs de tournoi automatiquement."""
    try:
        tournament = Tournament.objects.get(id=tournament_id)
        
        if tournament.status != 'ongoing':
            return {'error': 'Tournament not ongoing'}
        
        # Logique de gestion des tournois
        # (Implémentation simplifiée - à développer selon les besoins)
        
        # Vérifier les matchs en cours
        ongoing_matches = Game.objects.filter(
            # Critères pour identifier les matchs de tournoi
            # À adapter selon l'implémentation des tournois
            status='playing',
            created_at__gte=tournament.start_date
        )
        
        completed_matches = 0
        
        for match in ongoing_matches:
            if match.status == 'finished':
                # Traiter le résultat du match
                completed_matches += 1
        
        logger.info(f"Traité {completed_matches} matchs pour le tournoi {tournament.name}")
        return {'tournament': tournament.name, 'matches_processed': completed_matches}
        
    except Tournament.DoesNotExist:
        logger.error(f"Tournoi non trouvé: {tournament_id}")
        return {'error': 'tournament_not_found'}
    except Exception as exc:
        logger.error(f"Erreur lors du traitement des matchs de tournoi: {exc}")
        self.retry(countdown=300, exc=exc)


@shared_task(bind=True, max_retries=3)
def backup_game_data(self):
    """Sauvegarder les données de jeu importantes."""
    try:
        import json
        from django.core import serializers
        from django.conf import settings
        import os
        
        backup_date = timezone.now().strftime('%Y%m%d_%H%M%S')
        backup_dir = os.path.join(settings.MEDIA_ROOT, 'backups', 'games')
        os.makedirs(backup_dir, exist_ok=True)
        
        # Sauvegarder les parties terminées récemment
        recent_games = Game.objects.filter(
            finished_at__gte=timezone.now() - timedelta(days=7),
            status='finished'
        )
        
        games_backup_file = os.path.join(backup_dir, f'games_{backup_date}.json')
        with open(games_backup_file, 'w') as f:
            serialized_games = serializers.serialize('json', recent_games)
            f.write(serialized_games)
        
        # Sauvegarder les classements actuels
        leaderboards = Leaderboard.objects.all()
        leaderboards_backup_file = os.path.join(backup_dir, f'leaderboards_{backup_date}.json')
        with open(leaderboards_backup_file, 'w') as f:
            serialized_leaderboards = serializers.serialize('json', leaderboards)
            f.write(serialized_leaderboards)
        
        logger.info(f"Sauvegarde créée: {backup_date}")
        return {
            'backup_date': backup_date,
            'games_backed_up': recent_games.count(),
            'leaderboards_backed_up': leaderboards.count()
        }
        
    except Exception as exc:
        logger.error(f"Erreur lors de la sauvegarde: {exc}")
        self.retry(countdown=300, exc=exc)


@shared_task(bind=True, max_retries=3)
def calculate_user_statistics(self, user_id: int):
    """Calculer les statistiques détaillées d'un utilisateur."""
    try:
        user = User.objects.get(id=user_id)
        
        # Calculer les statistiques complètes
        stats = {}
        
        # Statistiques générales
        total_games = Game.objects.filter(
            Q(player1=user) | Q(player2=user),
            status='finished'
        ).count()
        
        total_wins = Game.objects.filter(winner=user).count()
        total_losses = total_games - total_wins
        
        win_rate = (total_wins / total_games * 100) if total_games > 0 else 0
        
        # Statistiques financières
        total_bet = Game.objects.filter(
            Q(player1=user) | Q(player2=user),
            status='finished'
        ).aggregate(total=Sum('bet_amount'))['total'] or 0
        
        total_winnings = Game.objects.filter(
            winner=user
        ).aggregate(total=Sum('winner_prize'))['total'] or 0
        
        net_profit = total_winnings - total_bet
        
        # Statistiques par type de jeu
        game_type_stats = {}
        for game_type in GameType.objects.filter(is_active=True):
            type_games = Game.objects.filter(
                Q(player1=user) | Q(player2=user),
                game_type=game_type,
                status='finished'
            ).count()
            
            type_wins = Game.objects.filter(
                winner=user,
                game_type=game_type
            ).count()
            
            if type_games > 0:
                game_type_stats[game_type.name] = {
                    'games': type_games,
                    'wins': type_wins,
                    'losses': type_games - type_wins,
                    'win_rate': (type_wins / type_games * 100)
                }
        
        # Sauvegarder les statistiques (cache ou modèle dédié)
        from django.core.cache import cache
        cache_key = f'user_stats_{user_id}'
        
        stats = {
            'total_games': total_games,
            'total_wins': total_wins,
            'total_losses': total_losses,
            'win_rate': win_rate,
            'total_bet': float(total_bet),
            'total_winnings': float(total_winnings),
            'net_profit': float(net_profit),
            'game_type_stats': game_type_stats,
            'last_updated': timezone.now().isoformat()
        }
        
        cache.set(cache_key, stats, 3600)  # Cache 1 heure
        
        logger.info(f"Statistiques calculées pour l'utilisateur {user.username}")
        return stats
        
    except User.DoesNotExist:
        logger.error(f"Utilisateur non trouvé: {user_id}")
        return {'error': 'user_not_found'}
    except Exception as exc:
        logger.error(f"Erreur lors du calcul des statistiques: {exc}")
        self.retry(countdown=300, exc=exc)


# Tâches périodiques - Configuration pour Celery Beat
"""
Configuration à ajouter dans settings.py:

from celery.schedules import crontab

CELERY_BEAT_SCHEDULE = {
    'check-game-timeouts': {
        'task': 'apps.games.tasks.check_game_timeouts',
        'schedule': 30.0,  # Toutes les 30 secondes
    },
    'cleanup-expired-invitations': {
        'task': 'apps.games.tasks.cleanup_expired_invitations',
        'schedule': crontab(minute='*/10'),  # Toutes les 10 minutes
    },
    'cleanup-abandoned-games': {
        'task': 'apps.games.tasks.cleanup_abandoned_games',
        'schedule': crontab(minute='*/30'),  # Toutes les 30 minutes
    },
    'update-leaderboards': {
        'task': 'apps.games.tasks.update_leaderboards',
        'schedule': crontab(hour=2, minute=0),  # Tous les jours à 2h
    },
    'send-daily-report': {
        'task': 'apps.games.tasks.send_daily_game_report',
        'schedule': crontab(hour=8, minute=0),  # Tous les jours à 8h
    },
    'backup-game-data': {
        'task': 'apps.games.tasks.backup_game_data',
        'schedule': crontab(hour=3, minute=0, day_of_week=1),  # Lundi à 3h
    },
}
"""
