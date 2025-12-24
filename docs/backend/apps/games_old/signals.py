# apps/games/signals.py
# ======================

from django.db.models.signals import post_save, pre_delete, post_delete
from django.dispatch import receiver
from django.utils import timezone
from django.core.cache import cache
from django.contrib.auth import get_user_model
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
import logging

from .models import Game, GameInvitation, GameReport, Tournament, TournamentParticipant
from apps.core.utils import log_user_activity
from .tasks import calculate_user_statistics

User = get_user_model()
logger = logging.getLogger(__name__)
channel_layer = get_channel_layer()


@receiver(post_save, sender=Game)
def game_post_save_handler(sender, instance, created, **kwargs):
    """Gestionnaire pour les modifications de parties."""
    
    if created:
        # Nouvelle partie créée
        logger.info(f"Nouvelle partie créée: {instance.room_code}")
        
        # Notifier via WebSocket si c'est une partie publique
        if not instance.is_private:
            async_to_sync(channel_layer.group_send)(
                "public_games",
                {
                    'type': 'game_created',
                    'game': {
                        'id': str(instance.id),
                        'room_code': instance.room_code,
                        'game_type': instance.game_type.display_name,
                        'bet_amount': str(instance.bet_amount),
                        'currency': instance.currency,
                        'creator': instance.player1.username if instance.player1 else 'Unknown'
                    }
                }
            )
        
        # Log de l'activité pour le créateur
        if instance.player1:
            log_user_activity(
                user=instance.player1,
                activity_type='game_created',
                description=f'Partie créée: {instance.game_type.display_name} - {instance.room_code}',
                metadata={
                    'game_id': str(instance.id),
                    'bet_amount': str(instance.bet_amount),
                    'currency': instance.currency
                }
            )
    
    else:
        # Partie mise à jour
        if hasattr(instance, '_previous_status'):
            old_status = instance._previous_status
            new_status = instance.status
            
            if old_status != new_status:
                _handle_game_status_change(instance, old_status, new_status)
        
        # Vérifier si un second joueur a rejoint
        if instance.player2 and not hasattr(instance, '_had_player2'):
            _handle_player_joined(instance)
        
        # Vérifier si la partie est terminée
        if instance.status == 'finished' and instance.winner:
            _handle_game_finished(instance)


def _handle_game_status_change(game, old_status, new_status):
    """Gérer les changements de statut de partie."""
    
    # Notifier via WebSocket
    async_to_sync(channel_layer.group_send)(
        f"game_{game.room_code}",
        {
            'type': 'status_changed',
            'old_status': old_status,
            'new_status': new_status,
            'game_id': str(game.id)
        }
    )
    
    # Actions spécifiques selon le changement de statut
    if new_status == 'playing':
        logger.info(f"Partie {game.room_code} commencée")
        
        # Log pour les deux joueurs
        if game.player1:
            log_user_activity(
                user=game.player1,
                activity_type='game_started',
                description=f'Partie commencée: {game.room_code}',
                metadata={'game_id': str(game.id), 'opponent': game.player2.username if game.player2 else None}
            )
        
        if game.player2:
            log_user_activity(
                user=game.player2,
                activity_type='game_started',
                description=f'Partie commencée: {game.room_code}',
                metadata={'game_id': str(game.id), 'opponent': game.player1.username if game.player1 else None}
            )
    
    elif new_status == 'cancelled':
        logger.info(f"Partie {game.room_code} annulée")
        _handle_game_cancelled(game)
    
    elif new_status == 'disputed':
        logger.warning(f"Partie {game.room_code} en litige")
        _handle_game_disputed(game)


def _handle_player_joined(game):
    """Gérer l'arrivée d'un second joueur."""
    
    logger.info(f"Joueur {game.player2.username} a rejoint la partie {game.room_code}")
    
    # Notifier via WebSocket
    async_to_sync(channel_layer.group_send)(
        f"game_{game.room_code}",
        {
            'type': 'player_joined',
            'player': game.player2.username,
            'game_id': str(game.id),
            'can_start': True
        }
    )
    
    # Retirer de la liste des parties en attente
    async_to_sync(channel_layer.group_send)(
        "public_games",
        {
            'type': 'game_full',
            'game_id': str(game.id),
            'room_code': game.room_code
        }
    )
    
    # Log pour le joueur qui rejoint
    log_user_activity(
        user=game.player2,
        activity_type='game_joined',
        description=f'Partie rejointe: {game.room_code}',
        metadata={
            'game_id': str(game.id),
            'creator': game.player1.username if game.player1 else None
        }
    )


def _handle_game_finished(game):
    """Gérer la fin d'une partie."""
    
    logger.info(f"Partie {game.room_code} terminée - Gagnant: {game.winner.username}")
    
    # Notifier via WebSocket
    async_to_sync(channel_layer.group_send)(
        f"game_{game.room_code}",
        {
            'type': 'game_finished',
            'winner': game.winner.username,
            'prize': str(game.winner_prize),
            'currency': game.currency,
            'game_id': str(game.id)
        }
    )
    
    # Log pour le gagnant
    log_user_activity(
        user=game.winner,
        activity_type='game_won',
        description=f'Partie gagnée: {game.room_code}',
        metadata={
            'game_id': str(game.id),
            'opponent': game.get_opponent(game.winner).username if game.get_opponent(game.winner) else None,
            'prize': str(game.winner_prize),
            'currency': game.currency
        }
    )
    
    # Log pour le perdant
    loser = game.get_opponent(game.winner)
    if loser:
        log_user_activity(
            user=loser,
            activity_type='game_lost',
            description=f'Partie perdue: {game.room_code}',
            metadata={
                'game_id': str(game.id),
                'opponent': game.winner.username,
                'bet_lost': str(game.bet_amount),
                'currency': game.currency
            }
        )
    
    # Déclencher le recalcul des statistiques des joueurs (async)
    if game.player1:
        calculate_user_statistics.delay(game.player1.id)
    if game.player2:
        calculate_user_statistics.delay(game.player2.id)
    
    # Invalider le cache des classements
    cache.delete_pattern('leaderboard_*')


def _handle_game_cancelled(game):
    """Gérer l'annulation d'une partie."""
    
    # Notifier via WebSocket
    async_to_sync(channel_layer.group_send)(
        f"game_{game.room_code}",
        {
            'type': 'game_cancelled',
            'message': 'La partie a été annulée',
            'game_id': str(game.id)
        }
    )
    
    # Log pour les joueurs
    players = [game.player1, game.player2]
    for player in players:
        if player:
            log_user_activity(
                user=player,
                activity_type='game_cancelled',
                description=f'Partie annulée: {game.room_code}',
                metadata={
                    'game_id': str(game.id),
                    'refunded': str(game.bet_amount) if game.bet_amount else '0'
                }
            )


def _handle_game_disputed(game):
    """Gérer une partie en litige."""
    
    # Notifier les administrateurs
    from django.core.mail import mail_admins
    
    subject = f'RUMO RUSH - Partie en litige: {game.room_code}'
    message = f"""
    Une partie est maintenant en litige:
    
    Code de partie: {game.room_code}
    Type de jeu: {game.game_type.display_name}
    Joueur 1: {game.player1.username if game.player1 else 'N/A'}
    Joueur 2: {game.player2.username if game.player2 else 'N/A'}
    Mise: {game.bet_amount} {game.currency}
    Créée le: {game.created_at.strftime('%d/%m/%Y %H:%M')}
    
    Veuillez examiner cette partie dans l'interface d'administration.
    """
    
    mail_admins(subject, message, fail_silently=True)
    
    # Notifier via WebSocket
    async_to_sync(channel_layer.group_send)(
        f"game_{game.room_code}",
        {
            'type': 'game_disputed',
            'message': 'Cette partie est maintenant en litige. Un administrateur va l\'examiner.',
            'game_id': str(game.id)
        }
    )


@receiver(post_save, sender=Game)
def save_previous_status(sender, instance, **kwargs):
    """Sauvegarder le statut précédent pour détecter les changements."""
    if instance.pk:
        # Récupérer l'instance depuis la DB pour avoir l'ancien statut
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            instance._previous_status = old_instance.status
        except sender.DoesNotExist:
            pass


@receiver(pre_delete, sender=Game)
def game_pre_delete_handler(sender, instance, **kwargs):
    """Gestionnaire avant suppression d'une partie."""
    
    logger.warning(f"Suppression de la partie {instance.room_code}")
    
    # Rembourser les joueurs si la partie n'est pas terminée
    if instance.status not in ['finished', 'cancelled'] and instance.bet_amount > 0:
        if instance.player1:
            instance.player1.update_balance(instance.currency, instance.bet_amount, 'add')
            log_user_activity(
                user=instance.player1,
                activity_type='game_deleted_refund',
                description=f'Remboursement suite à suppression de partie: {instance.room_code}',
                metadata={
                    'refunded_amount': str(instance.bet_amount),
                    'currency': instance.currency
                }
            )
        
        if instance.player2:
            instance.player2.update_balance(instance.currency, instance.bet_amount, 'add')
            log_user_activity(
                user=instance.player2,
                activity_type='game_deleted_refund',
                description=f'Remboursement suite à suppression de partie: {instance.room_code}',
                metadata={
                    'refunded_amount': str(instance.bet_amount),
                    'currency': instance.currency
                }
            )


@receiver(post_save, sender=GameInvitation)
def game_invitation_handler(sender, instance, created, **kwargs):
    """Gestionnaire pour les invitations de partie."""
    
    if created:
        # Nouvelle invitation
        logger.info(f"Nouvelle invitation de {instance.inviter.username} à {instance.invitee.username}")
        
        # Notifier l'invité via WebSocket
        async_to_sync(channel_layer.group_send)(
            f"user_{instance.invitee.id}",
            {
                'type': 'game_invitation',
                'invitation': {
                    'id': str(instance.id),
                    'game_code': instance.game.room_code,
                    'inviter': instance.inviter.username,
                    'game_type': instance.game.game_type.display_name,
                    'bet_amount': str(instance.game.bet_amount),
                    'currency': instance.game.currency,
                    'message': instance.message,
                    'expires_at': instance.expires_at.isoformat()
                }
            }
        )
        
        # Log pour l'inviteur
        log_user_activity(
            user=instance.inviter,
            activity_type='invitation_sent',
            description=f'Invitation envoyée à {instance.invitee.username}',
            metadata={
                'game_id': str(instance.game.id),
                'invitee': instance.invitee.username
            }
        )
    
    else:
        # Invitation mise à jour (acceptée, refusée, etc.)
        if hasattr(instance, '_previous_status'):
            old_status = instance._previous_status
            new_status = instance.status
            
            if old_status != new_status:
                _handle_invitation_status_change(instance, old_status, new_status)


def _handle_invitation_status_change(invitation, old_status, new_status):
    """Gérer les changements de statut d'invitation."""
    
    if new_status == 'accepted':
        logger.info(f"Invitation acceptée par {invitation.invitee.username}")
        
        # Notifier l'inviteur
        async_to_sync(channel_layer.group_send)(
            f"user_{invitation.inviter.id}",
            {
                'type': 'invitation_accepted',
                'invitee': invitation.invitee.username,
                'game_code': invitation.game.room_code,
                'game_id': str(invitation.game.id)
            }
        )
        
        # Log pour l'invité
        log_user_activity(
            user=invitation.invitee,
            activity_type='invitation_accepted',
            description=f'Invitation acceptée de {invitation.inviter.username}',
            metadata={
                'game_id': str(invitation.game.id),
                'inviter': invitation.inviter.username
            }
        )
    
    elif new_status == 'declined':
        logger.info(f"Invitation refusée par {invitation.invitee.username}")
        
        # Notifier l'inviteur
        async_to_sync(channel_layer.group_send)(
            f"user_{invitation.inviter.id}",
            {
                'type': 'invitation_declined',
                'invitee': invitation.invitee.username,
                'game_code': invitation.game.room_code
            }
        )
        
        # Log pour l'invité
        log_user_activity(
            user=invitation.invitee,
            activity_type='invitation_declined',
            description=f'Invitation refusée de {invitation.inviter.username}',
            metadata={
                'game_id': str(invitation.game.id),
                'inviter': invitation.inviter.username
            }
        )


@receiver(post_save, sender=GameReport)
def game_report_handler(sender, instance, created, **kwargs):
    """Gestionnaire pour les signalements de partie."""
    
    if created:
        logger.warning(f"Nouveau signalement par {instance.reporter.username} contre {instance.reported_user.username}")
        
        # Notifier les administrateurs
        from django.core.mail import mail_admins
        
        subject = f'RUMO RUSH - Nouveau signalement: {instance.get_report_type_display()}'
        message = f"""
        Un nouveau signalement a été créé:
        
        Signalant: {instance.reporter.username}
        Utilisateur signalé: {instance.reported_user.username}
        Type: {instance.get_report_type_display()}
        Partie: {instance.game.room_code}
        Description: {instance.description}
        
        Veuillez examiner ce signalement dans l'interface d'administration.
        """
        
        mail_admins(subject, message, fail_silently=True)
        
        # Log pour le signalant
        log_user_activity(
            user=instance.reporter,
            activity_type='report_submitted',
            description=f'Signalement créé contre {instance.reported_user.username}',
            metadata={
                'report_id': str(instance.id),
                'report_type': instance.report_type,
                'game_id': str(instance.game.id)
            }
        )
        
        # Vérifier si l'utilisateur signalé a beaucoup de rapports
        recent_reports = GameReport.objects.filter(
            reported_user=instance.reported_user,
            created_at__gte=timezone.now() - timezone.timedelta(hours=24)
        ).count()
        
        if recent_reports >= 3:  # Seuil d'alerte
            logger.critical(f"Utilisateur {instance.reported_user.username} a {recent_reports} signalements en 24h")
            
            # Notifier les administrateurs d'urgence
            subject = f'URGENT - Utilisateur avec multiples signalements: {instance.reported_user.username}'
            message = f"""
            ATTENTION: L'utilisateur {instance.reported_user.username} a reçu {recent_reports} signalements 
            dans les dernières 24 heures.
            
            Une action administrative immédiate pourrait être nécessaire.
            """
            
            mail_admins(subject, message, fail_silently=True)


@receiver(post_save, sender=Tournament)
def tournament_handler(sender, instance, created, **kwargs):
    """Gestionnaire pour les tournois."""
    
    if created:
        logger.info(f"Nouveau tournoi créé: {instance.name}")
        
        # Notifier via WebSocket (canal public des tournois)
        async_to_sync(channel_layer.group_send)(
            "tournaments",
            {
                'type': 'tournament_created',
                'tournament': {
                    'id': str(instance.id),
                    'name': instance.name,
                    'game_type': instance.game_type.display_name,
                    'entry_fee': str(instance.entry_fee),
                    'currency': instance.currency,
                    'max_participants': instance.max_participants,
                    'start_date': instance.start_date.isoformat(),
                    'registration_end': instance.registration_end.isoformat()
                }
            }
        )
        
        # Log pour l'organisateur
        log_user_activity(
            user=instance.organizer,
            activity_type='tournament_created',
            description=f'Tournoi créé: {instance.name}',
            metadata={
                'tournament_id': str(instance.id),
                'entry_fee': str(instance.entry_fee),
                'max_participants': instance.max_participants
            }
        )
    
    else:
        # Tournoi mis à jour
        if hasattr(instance, '_previous_status'):
            old_status = instance._previous_status
            new_status = instance.status
            
            if old_status != new_status:
                _handle_tournament_status_change(instance, old_status, new_status)


def _handle_tournament_status_change(tournament, old_status, new_status):
    """Gérer les changements de statut de tournoi."""
    
    if new_status == 'ongoing':
        logger.info(f"Tournoi {tournament.name} a commencé")
        
        # Notifier tous les participants
        participants = tournament.participants.select_related('user')
        
        for participant in participants:
            async_to_sync(channel_layer.group_send)(
                f"user_{participant.user.id}",
                {
                    'type': 'tournament_started',
                    'tournament': {
                        'id': str(tournament.id),
                        'name': tournament.name
                    }
                }
            )
            
            log_user_activity(
                user=participant.user,
                activity_type='tournament_started',
                description=f'Tournoi commencé: {tournament.name}',
                metadata={'tournament_id': str(tournament.id)}
            )
    
    elif new_status == 'finished':
        logger.info(f"Tournoi {tournament.name} terminé")
        _handle_tournament_finished(tournament)


def _handle_tournament_finished(tournament):
    """Gérer la fin d'un tournoi."""
    
    # Notifier tous les participants des résultats finaux
    participants = tournament.participants.select_related('user').order_by('final_position')
    
    for participant in participants:
        if participant.final_position:
            async_to_sync(channel_layer.group_send)(
                f"user_{participant.user.id}",
                {
                    'type': 'tournament_finished',
                    'tournament': {
                        'id': str(tournament.id),
                        'name': tournament.name,
                        'final_position': participant.final_position
                    }
                }
            )
            
            activity_type = 'tournament_won' if participant.final_position == 1 else 'tournament_finished'
            description = f'Tournoi terminé: {tournament.name} - Position: {participant.final_position}'
            
            log_user_activity(
                user=participant.user,
                activity_type=activity_type,
                description=description,
                metadata={
                    'tournament_id': str(tournament.id),
                    'final_position': participant.final_position
                }
            )


@receiver(post_save, sender=TournamentParticipant)
def tournament_participant_handler(sender, instance, created, **kwargs):
    """Gestionnaire pour les participants de tournoi."""
    
    if created:
        logger.info(f"Nouveau participant au tournoi {instance.tournament.name}: {instance.user.username}")
        
        # Notifier l'organisateur
        async_to_sync(channel_layer.group_send)(
            f"user_{instance.tournament.organizer.id}",
            {
                'type': 'tournament_registration',
                'participant': instance.user.username,
                'tournament': {
                    'id': str(instance.tournament.id),
                    'name': instance.tournament.name,
                    'current_participants': instance.tournament.participants.count(),
                    'max_participants': instance.tournament.max_participants
                }
            }
        )
        
        # Log pour le participant
        log_user_activity(
            user=instance.user,
            activity_type='tournament_registered',
            description=f'Inscription au tournoi: {instance.tournament.name}',
            metadata={
                'tournament_id': str(instance.tournament.id),
                'entry_fee': str(instance.tournament.entry_fee)
            }
        )
        
        # Vérifier si le tournoi est complet
        if instance.tournament.participants.count() >= instance.tournament.max_participants:
            # Le tournoi peut maintenant commencer (selon les règles)
            logger.info(f"Tournoi {instance.tournament.name} est complet")


# Signal pour nettoyer le cache quand nécessaire
@receiver([post_save, post_delete], sender=Game)
def invalidate_game_cache(sender, **kwargs):
    """Invalider le cache relatif aux jeux."""
    
    # Invalider les caches de statistiques
    cache.delete_pattern('game_stats_*')
    cache.delete_pattern('user_stats_*')
    cache.delete_pattern('leaderboard_*')
    
    # Invalider le cache des parties en attente
    cache.delete('waiting_games')


@receiver([post_save, post_delete], sender=Tournament)
def invalidate_tournament_cache(sender, **kwargs):
    """Invalider le cache relatif aux tournois."""
    
    cache.delete_pattern('tournament_*')
    cache.delete('active_tournaments')


# Configuration des signaux personnalisés
from django.dispatch import Signal

# Signaux personnalisés pour l'application
game_started = Signal()
game_finished = Signal()
player_timeout = Signal()
suspicious_activity = Signal()

# Exemple d'utilisation des signaux personnalisés
@receiver(suspicious_activity)
def handle_suspicious_activity(sender, user, activity_type, details, **kwargs):
    """Gérer les activités suspectes."""
    
    logger.warning(f"Activité suspecte détectée pour {user.username}: {activity_type}")
    
    # Logique de gestion des activités suspectes
    # (par exemple, bloquer temporairement l'utilisateur, alerter les admins, etc.)
    
    from django.core.mail import mail_admins
    
    subject = f'RUMO RUSH - Activité suspecte: {user.username}'
    message = f"""
    Activité suspecte détectée:
    
    Utilisateur: {user.username}
    Type d'activité: {activity_type}
    Détails: {details}
    Heure: {timezone.now().strftime('%d/%m/%Y %H:%M:%S')}
    
    Veuillez examiner ce compte dans l'interface d'administration.
    """
    
    mail_admins(subject, message, fail_silently=True)


# Fonction utilitaire pour déclencher les signaux personnalisés
def trigger_suspicious_activity(user, activity_type, details):
    """Déclencher le signal d'activité suspecte."""
    suspicious_activity.send(
        sender=None,
        user=user,
        activity_type=activity_type,
        details=details
    )


# Initialisation des signaux
def connect_signals():
    """Connecter tous les signaux de l'application games."""
    
    # Les signaux sont automatiquement connectés via les décorateurs @receiver
    # Cette fonction peut être utilisée pour des connexions manuelles si nécessaire
    
    logger.info("Signaux de l'application games connectés")


# Auto-import pour s'assurer que les signaux sont connectés
def ready():
    """Fonction appelée quand l'application est prête."""
    connect_signals()
