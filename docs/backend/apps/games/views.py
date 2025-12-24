# apps/games/views.py
# ====================
from decimal import Decimal  # <-- ADD THIS IMPORT
from rest_framework import status, generics, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.utils import timezone
from django.db import transaction, models
from django.db.models import Q, Count, Sum, Avg
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters
from django.core.cache import cache
from django.conf import settings
from django.contrib.auth import get_user_model  # <-- AJOUT DE CET IMPORT
from rest_framework.serializers import ValidationError  # <-- AJOUT DE CET IMPORT
import logging

from .models import (
    GameType, Game, GameInvitation, GameReport,
    Tournament, TournamentParticipant, Leaderboard
)
from .serializers import (
    GameTypeSerializer, GameListSerializer, GameDetailSerializer,
    GameCreateSerializer, GameMoveSerializer, GameInvitationSerializer,
    GameReportSerializer, TournamentListSerializer, TournamentDetailSerializer,
    LeaderboardSerializer, GameStatisticsSerializer
)
from apps.core.permissions import IsOwnerOrReadOnly
from apps.core.utils import log_user_activity

logger = logging.getLogger(__name__)


class StandardPagination(PageNumberPagination):
    """Pagination standard pour les listes."""
    page_size = 20
    page_size_query_param = 'page_size'
    max_page_size = 100


from rest_framework import permissions
from decimal import Decimal

class GameTypeViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour les types de jeux."""
    
    serializer_class = GameTypeSerializer
    pagination_class = None
    
    # Autoriser tout le monde à accéder à cette ressource
    permission_classes = [permissions.AllowAny]
    
    def get_queryset(self):
        # Initialiser les types de jeux s'ils n'existent pas
        self._ensure_game_types_exist()
        
        queryset = GameType.objects.filter(is_active=True).order_by('display_name')
        category = self.request.query_params.get('category')
        if category:
            queryset = queryset.filter(category=category)
        return queryset
    
    def _ensure_game_types_exist(self):
        """Créer les types de jeux par défaut s'ils n'existent pas."""
        if GameType.objects.filter(is_active=True).exists():
            return  # Les types de jeux existent déjà
        
        default_game_types = [
            {
                'name': 'chess',
                'display_name': 'Échecs',
                'description': 'Jeu de stratégie classique opposant deux armées sur un échiquier 8x8.',
                'category': 'strategy',
                'min_players': 2,
                'max_players': 2,
                'estimated_duration': 30,
                'min_bet_fcfa': Decimal('500'),
                'max_bet_fcfa': Decimal('100000'),
                'is_active': True,
            },
            {
                'name': 'checkers',
                'display_name': 'Dames',
                'description': 'Jeu de dames traditionnel sur plateau 8x8.',
                'category': 'strategy',
                'min_players': 2,
                'max_players': 2,
                'estimated_duration': 25,
                'min_bet_fcfa': Decimal('500'),
                'max_bet_fcfa': Decimal('75000'),
                'is_active': True,
            },
            {
                'name': 'ludo',
                'display_name': 'Ludo',
                'description': 'Jeu de plateau familial avec 4 pions.',
                'category': 'board',
                'min_players': 2,
                'max_players': 4,
                'estimated_duration': 20,
                'min_bet_fcfa': Decimal('500'),
                'max_bet_fcfa': Decimal('50000'),
                'is_active': True,
            },
            {
                'name': 'cards',
                'display_name': 'Cartes (Rami)',
                'description': 'Jeu de cartes où il faut former des combinaisons.',
                'category': 'cards',
                'min_players': 2,
                'max_players': 6,
                'estimated_duration': 15,
                'min_bet_fcfa': Decimal('500'),
                'max_bet_fcfa': Decimal('60000'),
                'is_active': True,
            },
            {
                'name': 'dominos',
                'display_name': 'Dominos',
                'description': 'Jeu de dominos traditionnel.',
                'category': 'board',
                'min_players': 2,
                'max_players': 4,
                'estimated_duration': 18,
                'min_bet_fcfa': Decimal('500'),
                'max_bet_fcfa': Decimal('40000'),
                'is_active': True,
            },
        ]
        
        for data in default_game_types:
            GameType.objects.get_or_create(name=data['name'], defaults=data)
    
    @action(detail=False, methods=['get'])
    def categories(self, request):
        self._ensure_game_types_exist()
        categories = GameType.objects.filter(is_active=True).values_list(
            'category', flat=True
        ).distinct()
        return Response({
            'categories': [
                {'value': cat, 'label': dict(GameType.GAME_CATEGORIES)[cat]}
                for cat in categories
            ]
        })

class GameViewSet(viewsets.ModelViewSet):
    """ViewSet pour les parties."""
    
    serializer_class = GameListSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_fields = ['status', 'game_type', 'currency', 'is_private']
    search_fields = ['room_code', 'player1__username', 'player2__username']
    ordering_fields = ['created_at', 'bet_amount', 'started_at']
    ordering = ['-created_at']
    
    def get_queryset(self):
        """Obtenir les parties selon le contexte."""
        user = self.request.user
        
        if self.action == 'list':
            # Parties publiques ou parties de l'utilisateur
            return Game.objects.filter(
                Q(is_private=False) | Q(player1=user) | Q(player2=user)
            ).select_related(
                'game_type', 'player1', 'player2', 'current_player', 'winner'
            ).prefetch_related('invitations', 'reports')
        
        # Pour les autres actions, toutes les parties accessibles
        return Game.objects.filter(
            Q(is_private=False) | Q(player1=user) | Q(player2=user)
        ).select_related(
            'game_type', 'player1', 'player2', 'current_player', 'winner'
        )
    
    def get_serializer_class(self):
        """Choisir le serializer selon l'action."""
        if self.action == 'create':
            return GameCreateSerializer
        elif self.action in ['retrieve', 'update', 'partial_update']:
            return GameDetailSerializer
        return GameListSerializer
    
    def perform_create(self, serializer):
        """Créer une nouvelle partie et initialiser les couleurs pour chaque joueur dans game_data si Ludo."""
        with transaction.atomic():
            game = serializer.save()
            # Initialiser les mains si jeu de cartes
            if hasattr(game, 'game_type') and getattr(game.game_type, 'name', None) == 'cards':
                game.initialize_cards()
                game.save()
            # Initialiser les couleurs pour Ludo
            if hasattr(game, 'game_type') and getattr(game.game_type, 'name', None) == 'ludo':
                # Attribution automatique des couleurs (red, green, blue, yellow)
                colors = ['red', 'green', 'blue', 'yellow']
                player_ids = [str(game.player1.id)]
                if game.player2:
                    player_ids.append(str(game.player2.id))
                # Si plus de joueurs, à adapter
                game_data = game.game_data or {}
                game_data['player_colors'] = {pid: colors[i % 4] for i, pid in enumerate(player_ids)}
                game.game_data = game_data
                game.save()
            # Log de l'activité
            log_user_activity(
                user=self.request.user,
                activity_type='game_created',
                description=f'Partie créée: {game.game_type.display_name}',
                metadata={'game_id': str(game.id), 'room_code': game.room_code}
            )
    
    @action(detail=True, methods=['post'])
    def join(self, request, pk=None):
        """Rejoindre une partie et enregistrer la couleur choisie dans game_data (seulement pour player2)."""
        game = self.get_object()
        if not game:
            logger.error(f"Game with ID {pk} does not exist.")
            return Response({
                'error': _('La partie demandée n\'existe pas')
            }, status=status.HTTP_404_NOT_FOUND)

        # Seul player2 peut rejoindre et choisir une couleur
        if game.player1 == request.user:
            return Response({
                'error': 'Vous êtes déjà le créateur de cette partie'
            }, status=status.HTTP_400_BAD_REQUEST)

        # Initialiser game_data si nécessaire
        if not game.game_data:
            game.game_data = {}
        if 'player_colors' not in game.game_data:
            game.game_data['player_colors'] = {}
            
        player_colors = game.game_data['player_colors']
        user_id = str(request.user.id)
        
        # Vérifier si l'utilisateur a déjà une couleur
        if user_id in player_colors:
            logger.info(f"User {request.user.username} already has color {player_colors[user_id]}")
        else:
            # Pour Ludo, exiger qu'une couleur soit spécifiée (seulement player2)
            if hasattr(game.game_type, 'name') and game.game_type.name.lower() == 'ludo':
                color = request.data.get('color')
                if not color:
                    return Response({
                        'error': 'Une couleur doit être choisie pour rejoindre cette partie Ludo.'
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                available_colors = ['red', 'green', 'blue', 'yellow'] if game.game_type.max_players == 4 else ['red', 'blue']
                taken_colors = set(player_colors.values())
                
                if color not in available_colors:
                    return Response({'error': 'Couleur invalide pour ce type de partie.'}, status=status.HTTP_400_BAD_REQUEST)
                if color in taken_colors:
                    return Response({'error': 'Couleur déjà prise.'}, status=status.HTTP_400_BAD_REQUEST)
                    
                player_colors[user_id] = color
                game.game_data['player_colors'] = player_colors
                logger.info(f"Player2 {request.user.username} chose color {color}")
            else:
                # Pour les autres jeux, assigner une couleur automatiquement
                color = request.data.get('color')
                available_colors = ['red', 'green', 'blue', 'yellow'] if game.game_type.max_players == 4 else ['red', 'blue']
                taken_colors = set(player_colors.values())
                
                if color:
                    # Couleur spécifiée
                    if color not in available_colors:
                        return Response({'error': 'Couleur invalide pour ce type de partie.'}, status=status.HTTP_400_BAD_REQUEST)
                    if color in taken_colors:
                        return Response({'error': 'Couleur déjà prise.'}, status=status.HTTP_400_BAD_REQUEST)
                else:
                    # Auto-assignation de la première couleur disponible pour les autres jeux
                    available = [c for c in available_colors if c not in taken_colors]
                    if not available:
                        return Response({'error': 'Aucune couleur disponible.'}, status=status.HTTP_400_BAD_REQUEST)
                    color = available[0]
                    
                player_colors[user_id] = color
                game.game_data['player_colors'] = player_colors
                logger.info(f"Assigned color {color} to user {request.user.username}")

        # IMPORTANT: Sauvegarder game_data AVANT join_game pour ne pas perdre la couleur
        game.save(update_fields=['game_data'])
        logger.info(f"✅ Saved game_data with player2 color: {game.game_data}")

        # Player2 rejoint la partie avec sa couleur choisie
        print(game)
        try:
            with transaction.atomic():
                join_success = game.join_game(request.user)
                if join_success:
                    log_user_activity(
                        user=request.user,
                        activity_type='game_joined',
                        description=f'Partie rejointe: {game.room_code}',
                        metadata={'game_id': str(game.id)}
                    )
                    serializer = GameDetailSerializer(game, context={'request': request})
                    logger.info(f"✅ Player {request.user.username} joined game {game.id} with color {color}")
                    return Response({
                        'success': True,
                        'message': _('Partie rejointe avec succès'),
                        'game': serializer.data
                    })
                else:
                    logger.error(f"❌ User {request.user.username} failed to join the game {game.room_code}.")
                    return Response({
                        'success': False,
                        'error': _('Impossible de rejoindre la partie')
                    }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"❌ Erreur lors de la jointure: {e}")
            return Response({
                'success': False,
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)

    
    @action(detail=True, methods=['post'])
    def start(self, request, pk=None):
        """Démarrer une partie."""
        game = self.get_object()
        
        if game.player1 != request.user:
            return Response({
                'error': _('Seul le créateur peut démarrer la partie')
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Pour Ludo, vérifier que tous les joueurs ont choisi une couleur
        if hasattr(game.game_type, 'name') and game.game_type.name in ['ludo', 'Ludo']:
            player_colors = game.game_data.get('player_colors', {}) if game.game_data else {}
            
            logger.info(f"Checking colors for start: player_colors={player_colors}")
            logger.info(f"Player1 ID: {game.player1.id}, Player2 ID: {game.player2.id if game.player2 else None}")
            
            # Vérifier que le créateur (player1) a une couleur
            if str(game.player1.id) not in player_colors:
                logger.error(f"Player1 {game.player1.username} has no color assigned")
                return Response({
                    'error': _('Le créateur doit choisir une couleur avant de démarrer')
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Vérifier que le second joueur (s'il existe) a une couleur
            if game.player2 and str(game.player2.id) not in player_colors:
                logger.error(f"Player2 {game.player2.username} has no color assigned")
                return Response({
                    'error': _('Tous les joueurs doivent choisir une couleur avant de démarrer')
                }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                game.start_game()
                # Recharge l'instance depuis la base pour avoir game_data à jour
                game.refresh_from_db()
                # Log de l'activité pour les deux joueurs
                log_user_activity(
                    user=request.user,
                    activity_type='game_started',
                    description=f'Partie démarrée: {game.room_code}',
                    metadata={'game_id': str(game.id)}
                )
                serializer = GameDetailSerializer(game, context={'request': request})
                return Response({
                    'message': _('Partie démarrée avec succès'),
                    'game': serializer.data
                })
                
        except Exception as e:
            logger.error(f"Erreur lors du démarrage: {e}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], url_path='my-games')
    def my_games(self, request):
        """Récupérer les parties de l'utilisateur connecté."""
        user = request.user
        games = Game.objects.filter(
            Q(player1=user) | Q(player2=user)
        ).select_related(
            'game_type', 'player1', 'player2', 'current_player', 'winner'
        ).order_by('-created_at')
        
        page = self.paginate_queryset(games)
        if page is not None:
            serializer = GameListSerializer(page, many=True, context={'request': request})
            return self.get_paginated_response(serializer.data)
        
        serializer = GameListSerializer(games, many=True, context={'request': request})
        return Response({
            'success': True,
            'data': serializer.data
        })
    
    @action(detail=True, methods=['post'])
    def move(self, request, pk=None):
        """Effectuer un mouvement dans la partie."""
        game = self.get_object()
        
        logger.info(f"🎯 === MOVE ACTION CALLED === User: {request.user.username}, Game: {game.id}")
        logger.info(f"🎯 Request data: {request.data}")
        logger.info(f"🎯 Request method: {request.method}")
        logger.info(f"🎯 Content-Type: {request.content_type}")
        
        if game.status != 'playing':
            logger.error(f"Game status is {game.status}, not playing")
            return Response({
                'error': _('La partie n\'est pas en cours')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if request.user not in [game.player1, game.player2]:
            logger.error(f"User {request.user.username} not in game players")
            return Response({
                'error': _('Vous ne participez pas à cette partie')
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = GameMoveSerializer(data=request.data, context={'game': game})
        if serializer.is_valid():
            try:
                with transaction.atomic():
                    # make_move returns [success, message, game_data]
                    result = game.make_move(request.user, serializer.validated_data['move_data'])
                    success = result[0] if isinstance(result, list) else result
                    
                    if success:
                        # Broadcast game state via WebSocket
                        from channels.layers import get_channel_layer
                        from asgiref.sync import async_to_sync
                        
                        channel_layer = get_channel_layer()
                        room_group_name = f'game_{game.room_code}'
                        
                        logger.info(f"📡 Broadcasting game state update to {room_group_name} after move")
                        
                        # Rafraîchir game depuis DB pour avoir les dernières données
                        game.refresh_from_db()
                        serializer_ws = GameDetailSerializer(game, context={'request': request})
                        
                        # Convertir les Decimal en float pour msgpack (WebSocket)
                        game_state_data = serializer_ws.data
                        from decimal import Decimal
                        def convert_decimals(obj):
                            if isinstance(obj, dict):
                                return {k: convert_decimals(v) for k, v in obj.items()}
                            elif isinstance(obj, list):
                                return [convert_decimals(item) for item in obj]
                            elif isinstance(obj, Decimal):
                                return float(obj)
                            return obj
                        
                        game_state_data = convert_decimals(game_state_data)
                        
                        async_to_sync(channel_layer.group_send)(
                            room_group_name,
                            {
                                'type': 'game_state_update',
                                'data': game_state_data
                            }
                        )
                        
                        serializer_response = GameDetailSerializer(game, context={'request': request})
                        return Response({
                            'message': _('Mouvement effectué avec succès'),
                            'game': serializer_response.data
                        })
                    else:
                        error_message = result[1] if isinstance(result, list) and len(result) > 1 else _('Mouvement invalide')
                        logger.error(f"Game.make_move returned False for {request.user.username}: {error_message}")
                        return Response({
                            'error': error_message
                        }, status=status.HTTP_400_BAD_REQUEST)
                        
            except Exception as e:
                logger.error(f"Erreur lors du mouvement: {e}")
                import traceback
                logger.error(f"Traceback: {traceback.format_exc()}")
                return Response({
                    'error': str(e)
                }, status=status.HTTP_400_BAD_REQUEST)
        
        logger.error(f"Serializer errors: {serializer.errors}")
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def surrender(self, request, pk=None):
        """Abandonner la partie."""
        game = self.get_object()
        
        if game.status != 'playing':
            return Response({
                'error': _('La partie n\'est pas en cours')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if request.user not in [game.player1, game.player2]:
            return Response({
                'error': _('Vous ne participez pas à cette partie')
            }, status=status.HTTP_403_FORBIDDEN)
        
        try:
            with transaction.atomic():
                # Déterminer le gagnant (l'adversaire)
                winner = game.get_opponent(request.user)
                game.end_game(winner, reason='surrender')
                
                # Log de l'activité
                log_user_activity(
                    user=request.user,
                    activity_type='game_lost',
                    description=f'Partie abandonnée: {game.room_code}',
                    metadata={'game_id': str(game.id), 'reason': 'surrender'}
                )
                
                serializer = GameDetailSerializer(game, context={'request': request})
                return Response({
                    'message': _('Partie abandonnée'),
                    'game': serializer.data
                })
                
        except Exception as e:
            logger.error(f"Erreur lors de l'abandon: {e}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Annuler une partie."""
        game = self.get_object()
        
        if game.player1 != request.user:
            return Response({
                'error': _('Seul le créateur peut annuler la partie')
            }, status=status.HTTP_403_FORBIDDEN)
        
        if game.status not in ['waiting', 'ready']:
            return Response({
                'error': _('Seules les parties en attente peuvent être annulées')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                game.cancel_game(reason='cancelled_by_creator')
                
                # Log de l'activité
                log_user_activity(
                    user=request.user,
                    activity_type='game_cancelled',
                    description=f'Partie annulée: {game.room_code}',
                    metadata={'game_id': str(game.id)}
                )
                
                return Response({
                    'message': _('Partie annulée avec succès')
                })
                
        except Exception as e:
            logger.error(f"Erreur lors de l'annulation: {e}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def waiting(self, request):
        """Obtenir les parties en attente de joueurs."""
        games = self.get_queryset().filter(
            status='waiting',
            is_private=False
        ).exclude(player1=request.user)[:10]
        
        serializer = self.get_serializer(games, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_games(self, request):
        """Obtenir les parties de l'utilisateur."""
        games = self.get_queryset().filter(
            Q(player1=request.user) | Q(player2=request.user)
        ).order_by('-created_at')
        
        # Filtrer par statut si spécifié
        status_filter = request.query_params.get('status')
        if status_filter:
            games = games.filter(status=status_filter)
        
        page = self.paginate_queryset(games)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(games, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def spectate(self, request, pk=None):
        """Obtenir les données pour spectateur."""
        game = self.get_object()
        
        if not game.spectators_allowed:
            return Response({
                'error': _('Les spectateurs ne sont pas autorisés pour cette partie')
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Version spectateur avec données limitées
        data = GameDetailSerializer(game, context={'request': request}).data
        
        # Masquer certaines informations sensibles
        spectator_data = {
            'id': data['id'],
            'room_code': data['room_code'],
            'game_type': data['game_type'],
            'status': data['status'],
            'status_display': data['status_display'],
            'players': {
                'player1': {'username': data['player1']['username']} if data['player1'] else None,
                'player2': {'username': data['player2']['username']} if data['player2'] else None,
                'current_player': {'username': data['current_player']['username']} if data['current_player'] else None,
            },
            'game_data': data['game_data'],
            'move_history': data['move_history'],
            'started_at': data['started_at'],
            'winner': {'username': data['winner']['username']} if data['winner'] else None,
        }
        
        return Response(spectator_data)



class TournamentViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour les tournois."""
    
    queryset = Tournament.objects.all().select_related(
        'game_type', 'organizer'
    ).prefetch_related('participants').order_by('-start_date')
    
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['status', 'game_type', 'tournament_type']
    search_fields = ['name', 'description']
    
    def get_serializer_class(self):
        """Choisir le serializer selon l'action."""
        if self.action == 'retrieve':
            return TournamentDetailSerializer
        return TournamentListSerializer
    
    @action(detail=True, methods=['post'])
    def register(self, request, pk=None):
        """S'inscrire à un tournoi."""
        tournament = self.get_object()
        
        # Vérifications
        if tournament.status != 'registration':
            return Response({
                'error': _('Les inscriptions ne sont pas ouvertes')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if tournament.participants.count() >= tournament.max_participants:
            return Response({
                'error': _('Tournoi complet')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        if tournament.participants.filter(user=request.user).exists():
            return Response({
                'error': _('Vous êtes déjà inscrit')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Vérifier le solde pour les frais d'inscription
        if tournament.entry_fee > 0:
            balance = request.user.get_balance(tournament.currency)
            if balance < tournament.entry_fee:
                return Response({
                    'error': _('Solde insuffisant')
                }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            with transaction.atomic():
                # Débiter les frais d'inscription
                if tournament.entry_fee > 0:
                    request.user.update_balance(
                        tournament.currency,
                        tournament.entry_fee,
                        'subtract'
                    )
                
                # Créer la participation
                participant = TournamentParticipant.objects.create(
                    tournament=tournament,
                    user=request.user
                )
                
                # Log de l'activité
                log_user_activity(
                    user=request.user,
                    activity_type='tournament_registered',
                    description=f'Inscription au tournoi: {tournament.name}',
                    metadata={'tournament_id': str(tournament.id)}
                )
                
                return Response({
                    'message': _('Inscription réussie'),
                    'participant_id': str(participant.id)
                })
                
        except Exception as e:
            logger.error(f"Erreur inscription tournoi: {e}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['post'])
    def unregister(self, request, pk=None):
        """Se désinscrire d'un tournoi."""
        tournament = self.get_object()
        
        try:
            participant = tournament.participants.get(user=request.user)
            
            if tournament.status != 'registration':
                return Response({
                    'error': _('Impossible de se désinscrire après le début')
                }, status=status.HTTP_400_BAD_REQUEST)
            
            with transaction.atomic():
                # Rembourser les frais d'inscription
                if tournament.entry_fee > 0:
                    request.user.update_balance(
                        tournament.currency,
                        tournament.entry_fee,
                        'add'
                    )
                
                participant.delete()
                
                # Log de l'activité
                log_user_activity(
                    user=request.user,
                    activity_type='tournament_unregistered',
                    description=f'Désinscription du tournoi: {tournament.name}',
                    metadata={'tournament_id': str(tournament.id)}
                )
                
                return Response({
                    'message': _('Désinscription réussie')
                })
                
        except TournamentParticipant.DoesNotExist:
            return Response({
                'error': _('Vous n\'êtes pas inscrit à ce tournoi')
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception as e:
            logger.error(f"Erreur désinscription tournoi: {e}")
            return Response({
                'error': str(e)
            }, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'])
    def my_tournaments(self, request):
        """Obtenir les tournois de l'utilisateur."""
        tournaments = self.get_queryset().filter(
            participants__user=request.user
        ).distinct()
        
        serializer = self.get_serializer(tournaments, many=True)
        return Response(serializer.data)


class LeaderboardViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet pour les classements."""
    
    serializer_class = LeaderboardSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = StandardPagination
    
    def get_queryset(self):
        """Obtenir les classements selon le type."""
        leaderboard_type = self.request.query_params.get('type', 'global')
        game_type_id = self.request.query_params.get('game_type')
        
        queryset = Leaderboard.objects.select_related(
            'user', 'game_type'
        ).filter(leaderboard_type=leaderboard_type).order_by('rank')
        
        if game_type_id and leaderboard_type == 'game_type':
            queryset = queryset.filter(game_type_id=game_type_id)
        
        return queryset[:100]  # Top 100
    
    @action(detail=False, methods=['get'])
    def my_position(self, request):
        """Obtenir la position de l'utilisateur."""
        if not request.user.is_authenticated:
            return Response({
                'error': _('Authentification requise')
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        leaderboard_type = request.query_params.get('type', 'global')
        game_type_id = request.query_params.get('game_type')
        
        try:
            position = Leaderboard.objects.get(
                user=request.user,
                leaderboard_type=leaderboard_type,
                game_type_id=game_type_id if leaderboard_type == 'game_type' else None
            )
            
            serializer = self.get_serializer(position)
            return Response(serializer.data)
            
        except Leaderboard.DoesNotExist:
            return Response({
                'message': _('Position non trouvée dans ce classement')
            }, status=status.HTTP_404_NOT_FOUND)


class GameStatisticsView(APIView):
    """Vue pour les statistiques de jeu."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Obtenir les statistiques de l'utilisateur."""
        # Utiliser le cache pour éviter les recalculs fréquents
        cache_key = f"user_stats_{request.user.id}"
        cached_stats = cache.get(cache_key)
        
        if cached_stats:
            return Response(cached_stats)
        
        # Calculer les statistiques
        serializer = GameStatisticsSerializer()
        stats = serializer.to_representation(request.user)
        
        # Mettre en cache pour 10 minutes
        cache.set(cache_key, stats, 600)
        
        return Response(stats)
    
    @action(detail=False, methods=['get'])
    def leaderboard(self, request):
        """Statistiques du classement global."""
        top_players = Leaderboard.objects.filter(
            leaderboard_type='global'
        ).select_related('user').order_by('rank')[:10]
        
        data = []
        for entry in top_players:
            data.append({
                'rank': entry.rank,
                'user': {
                    'username': entry.user.username,
                    'full_name': entry.user.full_name
                },
                'points': entry.points,
                'games_played': entry.games_played,
                'games_won': entry.games_won,
                'win_rate': entry.win_rate,
                'total_winnings': entry.total_winnings
            })
        
        return Response({
            'top_players': data,
            'updated_at': timezone.now()
        })


class GameSearchView(APIView):
    """Vue pour rechercher des parties."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request):
        """Rechercher des parties selon les critères."""
        room_code = request.query_params.get('room_code')
        
        if room_code:
            # Recherche par code de partie
            try:
                game = Game.objects.get(room_code__iexact=room_code)
                serializer = GameDetailSerializer(game, context={'request': request})
                return Response({
                    'found': True,
                    'game': serializer.data
                })
            except Game.DoesNotExist:
                return Response({
                    'found': False,
                    'message': _('Aucune partie trouvée avec ce code')
                })
        
        # Autres critères de recherche
        game_type = request.query_params.get('game_type')
        min_bet = request.query_params.get('min_bet')
        max_bet = request.query_params.get('max_bet')
        currency = request.query_params.get('currency', 'FCFA')
        
        queryset = Game.objects.filter(
            status='waiting',
            is_private=False
        ).exclude(player1=request.user)
        
        if game_type:
            queryset = queryset.filter(game_type__name=game_type)
        
        if min_bet:
            queryset = queryset.filter(bet_amount__gte=min_bet)
        
        if max_bet:
            queryset = queryset.filter(bet_amount__lte=max_bet)
        
        queryset = queryset.filter(currency=currency)
        
        games = queryset.select_related(
            'game_type', 'player1'
        ).order_by('-created_at')[:20]
        
        serializer = GameListSerializer(games, many=True, context={'request': request})
        return Response({
            'games': serializer.data,
            'count': len(games)
        })


class QuickMatchView(APIView):
    """Vue pour le matchmaking rapide."""
    
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """Trouver rapidement une partie."""
        # Validation des données d'entrée
        game_type = request.data.get('game_type')
        bet_amount = request.data.get('bet_amount')
        currency = request.data.get('currency', 'FCFA')
        
        # Validation plus stricte
        if not game_type:
            return Response({
                'error': _('Type de jeu requis')
            }, status=status.HTTP_400_BAD_REQUEST)
            
        if not bet_amount:
            return Response({
                'error': _('Montant de mise requis')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validation du montant
        try:
            bet_amount = Decimal(str(bet_amount))
            if bet_amount <= 0:
                return Response({
                    'error': _('Le montant de mise doit être positif')
                }, status=status.HTTP_400_BAD_REQUEST)
        except (ValueError, TypeError):
            return Response({
                'error': _('Montant de mise invalide')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Validation de la devise
        if currency not in ['FCFA', 'USD', 'EUR']:  # Ajustez selon vos devises
            return Response({
                'error': _('Devise non supportée')
            }, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            # Vérifier que le type de jeu existe
            try:
                print('typ', game_type)
                game_type_obj = GameType.objects.get(id=game_type, is_active=True)
            except GameType.DoesNotExist:
                return Response({
                    'error': _('Type de jeu invalide ou non disponible')
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Vérifier les fonds de l'utilisateur
            try:
                balance = request.user.get_balance(currency)
                if balance < bet_amount:
                    return Response({
                        'error': _('Solde insuffisant'),
                        'required': str(bet_amount),
                        'available': str(balance)
                    }, status=status.HTTP_400_BAD_REQUEST)
            except AttributeError:
                return Response({
                    'error': _('Erreur lors de la vérification du solde')
                }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
            # Chercher une partie existante
            existing_game = Game.objects.filter(
                game_type=game_type_obj,  # Utiliser l'objet au lieu du nom
                bet_amount=bet_amount,
                currency=currency,
                status='waiting',
                is_private=False
            ).exclude(player1=request.user).first()
            
            if existing_game:
                # Rejoindre la partie existante
                with transaction.atomic():
                    success = existing_game.join_game(request.user)
                    
                    if not success:
                        return Response({
                            'error': _('Impossible de rejoindre la partie')
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    # Log de l'activité
                    log_user_activity(
                        user=request.user,
                        activity_type='quick_match_joined',
                        description=f'Match rapide rejoint: {existing_game.room_code}',
                        metadata={'game_id': str(existing_game.id)}
                    )
                    
                    serializer = GameDetailSerializer(
                        existing_game, 
                        context={'request': request}
                    )
                    return Response({
                        'matched': True,
                        'joined_existing': True,
                        'game': serializer.data
                    })
            else:
                # Créer une nouvelle partie
                with transaction.atomic():
                    # Débiter la mise
                    try:
                        request.user.update_balance(currency, bet_amount, 'subtract')
                    except Exception as e:
                        return Response({
                            'error': _('Erreur lors du débit de la mise'),
                            'details': str(e)
                        }, status=status.HTTP_400_BAD_REQUEST)
                    
                    # Créer la partie
                    game = Game.objects.create(
                        game_type=game_type_obj,
                        player1=request.user,
                        bet_amount=bet_amount,
                        currency=currency,
                        status='waiting',
                        is_private=False,  # S'assurer que la partie est publique
                        spectators_allowed=True  # Permettre les spectateurs par défaut
                    )
                    
                    # Log de l'activité
                    log_user_activity(
                        user=request.user,
                        activity_type='quick_match_created',
                        description=f'Match rapide créé: {game.room_code}',
                        metadata={'game_id': str(game.id)}
                    )
                    
                    serializer = GameDetailSerializer(game, context={'request': request})
                    return Response({
                        'matched': False,
                        'created': True,
                        'game': serializer.data,
                        'message': _('Partie créée, en attente d\'un adversaire')
                    })
                    
        except Exception as e:
            logger.error(f"Erreur quick match pour {request.user.username}: {e}", exc_info=True)
            return Response({
                'error': _('Erreur interne du serveur'),
                'details': str(e) if settings.DEBUG else None
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Correction pour GameInvitationViewSet
class GameInvitationViewSet(viewsets.ModelViewSet):
    """ViewSet pour les invitations de partie."""
    
    serializer_class = GameInvitationSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardPagination
    
    def get_queryset(self):
        """Obtenir les invitations de l'utilisateur."""
        return GameInvitation.objects.filter(
            Q(inviter=self.request.user) | Q(invitee=self.request.user)
        ).select_related('game', 'inviter', 'invitee').order_by('-created_at')
    
    def perform_create(self, serializer):
        """Créer une nouvelle invitation."""
        game_id = self.request.data.get('game_id')
        invitee_id = self.request.data.get('invitee_id')
        
        try:
            game = Game.objects.get(id=game_id, player1=self.request.user)
            User = get_user_model()  # Correction ici
            invitee = User.objects.get(id=invitee_id)
            
            # Vérifier si l'invitation n'existe pas déjà
            existing = GameInvitation.objects.filter(
                game=game, invitee=invitee, status='pending'
            ).exists()
            
            if existing:
                raise ValidationError(_('Invitation déjà envoyée'))
            
            # Créer l'invitation avec expiration dans 24h
            expires_at = timezone.now() + timezone.timedelta(hours=24)
            
            invitation = serializer.save(
                game=game,
                inviter=self.request.user,
                invitee=invitee,
                expires_at=expires_at
            )
            
            # Log de l'activité
            log_user_activity(
                user=self.request.user,
                activity_type='invitation_sent',
                description=f'Invitation envoyée à {invitee.username}',
                metadata={'game_id': str(game.id), 'invitation_id': str(invitation.id)}
            )
            
        except Game.DoesNotExist:
            raise ValidationError(_('Partie introuvable ou non autorisée'))
        except get_user_model().DoesNotExist:  # Correction ici aussi
            raise ValidationError(_('Utilisateur introuvable'))


# Correction pour GameReportViewSet
class GameReportViewSet(viewsets.ModelViewSet):
    """ViewSet pour les signalements de partie."""
    
    serializer_class = GameReportSerializer
    permission_classes = [permissions.IsAuthenticated]
    pagination_class = StandardPagination
    
    def get_queryset(self):
        """Obtenir les signalements de l'utilisateur."""
        return GameReport.objects.filter(
            reporter=self.request.user
        ).select_related(
            'game', 'reporter', 'reported_user', 'resolved_by'
        ).order_by('-created_at')
    
    def perform_create(self, serializer):
        """Créer un nouveau signalement."""
        game_id = self.request.data.get('game_id')
        reported_user_id = self.request.data.get('reported_user_id')
        
        try:
            game = Game.objects.get(id=game_id)
            User = get_user_model()  # Correction ici
            reported_user = User.objects.get(id=reported_user_id)
            
            # Vérifier que l'utilisateur a participé à la partie
            if self.request.user not in [game.player1, game.player2]:
                raise ValidationError(_('Vous n\'avez pas participé à cette partie'))
            
            # Vérifier que l'utilisateur signalé a aussi participé
            if reported_user not in [game.player1, game.player2]:
                raise ValidationError(_('L\'utilisateur signalé n\'a pas participé à cette partie'))
            
            # Éviter l'auto-signalement
            if reported_user == self.request.user:
                raise ValidationError(_('Vous ne pouvez pas vous signaler vous-même'))
            
            report = serializer.save(
                game=game,
                reporter=self.request.user,
                reported_user=reported_user
            )
            
            # Log de l'activité
            log_user_activity(
                user=self.request.user,
                activity_type='report_submitted',
                description=f'Signalement créé contre {reported_user.username}',
                metadata={'game_id': str(game.id), 'report_id': str(report.id)}
            )
            
        except Game.DoesNotExist:
            raise ValidationError(_('Partie introuvable'))
        except get_user_model().DoesNotExist:  # Correction ici aussi
            raise ValidationError(_('Utilisateur introuvable'))

    def update(self, request, *args, **kwargs):
        """Met à jour la partie et enregistre la couleur dans game_data si présente."""
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        data = request.data.copy()

        # Gestion de la couleur pour Ludo
        color = data.get('color')
        if color:
            if color not in ['red', 'green', 'blue', 'yellow']:
                return Response({'error': 'Couleur invalide.'}, status=status.HTTP_400_BAD_REQUEST)
            game_data = instance.game_data or {}
            if 'player_colors' not in game_data:
                game_data['player_colors'] = {}
            player_colors = game_data['player_colors']
            if color in player_colors.values():
                return Response({'error': 'Couleur déjà prise.'}, status=status.HTTP_400_BAD_REQUEST)
            player_colors[str(request.user.id)] = color
            game_data['player_colors'] = player_colors
            instance.game_data = game_data
            instance.save()

        return super().update(request, *args, **kwargs)
