# apps/games/serializers.py - Updated version with icon field handling

from rest_framework import serializers
from .models import GameType, Game, GameInvitation, GameReport, Tournament, Leaderboard
from apps.accounts.serializers import UserSerializer

class GameTypeSerializer(serializers.ModelSerializer):
    """Serializer pour les types de jeux avec gestion d'icône."""
    
    # Ajouter un champ icon_emoji pour les émojis
    icon_emoji = serializers.SerializerMethodField()
    
    class Meta:
        model = GameType
        fields = [
            'id', 'name', 'display_name', 'description', 'category',
            'min_players', 'max_players', 'estimated_duration',
            'min_bet_fcfa', 'max_bet_fcfa', 'is_active',
            'icon', 'icon_emoji', 'rules_url'
        ]
    
    def get_icon_emoji(self, obj):
        """Retourner l'émoji selon le type de jeu."""
        icon_map = {
            'Échecs': '♟️',
            'Dames': '⚫',
            'Ludo': '🎲', 
            'Cartes': '🃏',
            'chess': '♟️',
            'checkers': '⚫',
            'ludo': '🎲',
            'cards': '🃏'
        }
        return icon_map.get(obj.name, '🎮')
    
    def to_representation(self, instance):
        """Modifier la représentation pour inclure l'icône."""
        data = super().to_representation(instance)
        # Utiliser l'émoji comme icône principale si pas d'image
        if not data.get('icon'):
            data['icon'] = data['icon_emoji']
        return data


class GameListSerializer(serializers.ModelSerializer):
    """Serializer pour la liste des parties."""
    
    game_type = GameTypeSerializer(read_only=True)
    player1 = UserSerializer(read_only=True)
    player2 = UserSerializer(read_only=True)
    current_player = UserSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    players_count = serializers.SerializerMethodField()
    max_players = serializers.SerializerMethodField()
    
    class Meta:
        model = Game
        fields = [
            'id', 'room_code', 'game_type', 'player1', 'player2', 
            'current_player', 'bet_amount', 'currency', 'total_pot',
            'status', 'status_display', 'players_count', 'max_players',
            'is_private', 'spectators_allowed', 'created_at', 'started_at'
        ]
    
    def get_players_count(self, obj):
        """Nombre de joueurs connectés."""
        count = 1  # player1 toujours présent
        if obj.player2:
            count += 1
        return count
    
    def get_max_players(self, obj):
        """Nombre maximum de joueurs."""
        return obj.game_type.max_players


class GameDetailSerializer(serializers.ModelSerializer):
    """Serializer détaillé pour une partie."""
    
    game_type = GameTypeSerializer(read_only=True)
    player1 = UserSerializer(read_only=True)
    player2 = UserSerializer(read_only=True)
    current_player = UserSerializer(read_only=True)
    winner = UserSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    players_count = serializers.SerializerMethodField()
    max_players = serializers.SerializerMethodField()
    can_join = serializers.SerializerMethodField()
    time_left = serializers.SerializerMethodField()
    
    class Meta:
        model = Game
        fields = [
            'id', 'room_code', 'game_type', 'player1', 'player2',
            'current_player', 'winner', 'bet_amount', 'currency',
            'total_pot', 'commission', 'winner_prize', 'status',
            'status_display', 'players_count', 'max_players',
            'can_join', 'game_data', 'move_history', 'turn_start_time',
            'turn_timeout', 'time_left', 'is_private', 'is_rated',
            'spectators_allowed', 'created_at', 'started_at',
            'finished_at', 'last_move_at'
        ]
    
    def get_players_count(self, obj):
        """Nombre de joueurs connectés."""
        count = 1
        if obj.player2:
            count += 1
        return count
    
    def get_max_players(self, obj):
        """Nombre maximum de joueurs."""
        return obj.game_type.max_players
    
    def get_can_join(self, obj):
        """Vérifier si l'utilisateur peut rejoindre."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        can_join, _ = obj.can_join(request.user)
        return can_join
    
    def get_time_left(self, obj):
        """Temps restant pour les joueurs."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return None
        
        return {
            'player1': obj.get_time_left(obj.player1) if obj.player1 else 0,
            'player2': obj.get_time_left(obj.player2) if obj.player2 else 0,
            'current_player': obj.get_time_left(request.user) if request.user in [obj.player1, obj.player2] else 0
        }
    
    def to_representation(self, instance):
        """Ajouter board_unicode pour les jeux de dames."""
        data = super().to_representation(instance)
        
        # Convertir les Decimal en float pour éviter les erreurs de sérialisation JSON
        from decimal import Decimal
        for field in ['bet_amount', 'total_pot', 'commission', 'winner_prize']:
            if field in data and isinstance(data[field], Decimal):
                data[field] = float(data[field])
        
        # 🎯 Pour Ludo, current_player doit venir de game_data (couleur), pas du modèle (User)
        if instance.game_type and instance.game_type.name.lower() == 'ludo':
            if 'game_data' in data and data['game_data']:
                # Remplacer current_player User par la couleur depuis game_data
                current_color = data['game_data'].get('current_player')
                if current_color:
                    data['current_player'] = current_color
                    # Optionnel: ajouter aussi le nom du joueur qui a cette couleur
                    player_colors = data['game_data'].get('player_colors', {})
                    for player_id, color in player_colors.items():
                        if color == current_color:
                            # Trouver le username correspondant
                            if str(instance.player1.id) == player_id:
                                data['current_player_name'] = instance.player1.username
                            elif instance.player2 and str(instance.player2.id) == player_id:
                                data['current_player_name'] = instance.player2.username
                            break
        
        # Si c'est un jeu de dames, ajouter la version Unicode du plateau
        if instance.game_type and instance.game_type.name.lower() == 'dames':
            if 'game_data' in data and data['game_data']:
                from apps.games.game_logic.checkers_competitive import convert_board_to_unicode
                data['game_data']['board_unicode'] = convert_board_to_unicode(data['game_data'])
        
        return data


class GameCreateSerializer(serializers.ModelSerializer):
    """Serializer pour créer une partie."""
    
    game_type_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = Game
        fields = [
            'game_type_id', 'bet_amount', 'currency', 'is_private',
            'spectators_allowed', 'is_rated'
        ]
    
    def validate_game_type_id(self, value):
        """Valider le type de jeu."""
        try:
            game_type = GameType.objects.get(id=value, is_active=True)
            return game_type
        except GameType.DoesNotExist:
            raise serializers.ValidationError("Type de jeu invalide ou inactif")
    
    def validate_bet_amount(self, value):
        """Valider le montant de la mise."""
        if value <= 0:
            raise serializers.ValidationError("Le montant de la mise doit être positif")
        return value
    
    def create(self, validated_data):
        """Créer une nouvelle partie."""
        game_type = validated_data.pop('game_type_id')
        request = self.context.get('request')
        
        # Vérifier les fonds
        user = request.user
        balance = user.get_balance(validated_data['currency'])
        if balance < validated_data['bet_amount']:
            raise serializers.ValidationError("Solde insuffisant")
        
        # Débiter la mise
        user.update_balance(
            validated_data['currency'],
            validated_data['bet_amount'],
            'subtract'
        )
        
        # Créer la partie
        game = Game.objects.create(
            game_type=game_type,
            player1=user,
            **validated_data
        )
        
        return game


class GameMoveSerializer(serializers.Serializer):
    """Serializer pour les mouvements."""
    
    move_data = serializers.JSONField()
    
    def validate_move_data(self, value):
        """Valider les données de mouvement."""
        game = self.context.get('game')
        if not game:
            raise serializers.ValidationError("Contexte de jeu manquant")
        
        # Validation basique - à étendre selon les règles de chaque jeu
        if not isinstance(value, dict):
            raise serializers.ValidationError("Les données de mouvement doivent être un objet")
        
        return value


class GameInvitationSerializer(serializers.ModelSerializer):
    """Serializer pour les invitations."""
    
    game = GameListSerializer(read_only=True)
    inviter = UserSerializer(read_only=True)
    invitee = UserSerializer(read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    is_expired = serializers.SerializerMethodField()
    
    class Meta:
        model = GameInvitation
        fields = [
            'id', 'game', 'inviter', 'invitee', 'status',
            'status_display', 'message', 'is_expired',
            'created_at', 'responded_at', 'expires_at'
        ]
    
    def get_is_expired(self, obj):
        """Vérifier si l'invitation a expiré."""
        from django.utils import timezone
        return timezone.now() > obj.expires_at


class GameReportSerializer(serializers.ModelSerializer):
    """Serializer pour les signalements."""
    
    game = GameListSerializer(read_only=True)
    reporter = UserSerializer(read_only=True)
    reported_user = UserSerializer(read_only=True)
    resolved_by = UserSerializer(read_only=True)
    report_type_display = serializers.CharField(source='get_report_type_display', read_only=True)
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    
    class Meta:
        model = GameReport
        fields = [
            'id', 'game', 'reporter', 'reported_user', 'resolved_by',
            'report_type', 'report_type_display', 'description',
            'evidence', 'status', 'status_display', 'admin_notes',
            'created_at', 'updated_at', 'resolved_at'
        ]


class TournamentListSerializer(serializers.ModelSerializer):
    """Serializer pour la liste des tournois."""
    
    game_type = GameTypeSerializer(read_only=True)
    organizer = UserSerializer(read_only=True)
    participants_count = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)
    tournament_type_display = serializers.CharField(source='get_tournament_type_display', read_only=True)
    
    class Meta:
        model = Tournament
        fields = [
            'id', 'name', 'description', 'game_type', 'organizer',
            'tournament_type', 'tournament_type_display', 'max_participants',
            'participants_count', 'entry_fee', 'currency', 'total_prize_pool',
            'winner_prize', 'runner_up_prize', 'registration_start',
            'registration_end', 'start_date', 'end_date', 'status',
            'status_display', 'created_at'
        ]
    
    def get_participants_count(self, obj):
        """Nombre de participants inscrits."""
        return obj.participants.count()


class TournamentDetailSerializer(TournamentListSerializer):
    """Serializer détaillé pour un tournoi."""
    
    from .models import TournamentParticipant
    
    participants = serializers.SerializerMethodField()
    is_registered = serializers.SerializerMethodField()
    can_register = serializers.SerializerMethodField()
    
    class Meta(TournamentListSerializer.Meta):
        fields = TournamentListSerializer.Meta.fields + [
            'participants', 'is_registered', 'can_register'
        ]
    
    def get_participants(self, obj):
        """Liste des participants avec leurs statistiques."""
        from .models import TournamentParticipant
        
        participants = TournamentParticipant.objects.filter(
            tournament=obj
        ).select_related('user').order_by('seed', 'registered_at')
        
        return [
            {
                'id': p.id,
                'user': UserSerializer(p.user).data,
                'seed': p.seed,
                'current_round': p.current_round,
                'is_eliminated': p.is_eliminated,
                'final_position': p.final_position,
                'registered_at': p.registered_at
            }
            for p in participants
        ]
    
    def get_is_registered(self, obj):
        """Vérifier si l'utilisateur est inscrit."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        return obj.participants.filter(user=request.user).exists()
    
    def get_can_register(self, obj):
        """Vérifier si l'utilisateur peut s'inscrire."""
        request = self.context.get('request')
        if not request or not request.user.is_authenticated:
            return False
        
        # Vérifications de base
        if obj.status != 'registration':
            return False
        
        if obj.participants.count() >= obj.max_participants:
            return False
        
        if obj.participants.filter(user=request.user).exists():
            return False
        
        # Vérifier les fonds pour les frais d'inscription
        if obj.entry_fee > 0:
            balance = request.user.get_balance(obj.currency)
            if balance < obj.entry_fee:
                return False
        
        return True


class LeaderboardSerializer(serializers.ModelSerializer):
    """Serializer pour les classements."""
    
    user = UserSerializer(read_only=True)
    game_type = GameTypeSerializer(read_only=True)
    leaderboard_type_display = serializers.CharField(source='get_leaderboard_type_display', read_only=True)
    
    class Meta:
        model = Leaderboard
        fields = [
            'id', 'user', 'leaderboard_type', 'leaderboard_type_display',
            'game_type', 'rank', 'points', 'games_played', 'games_won',
            'win_rate', 'total_winnings', 'period_start', 'period_end',
            'updated_at'
        ]


class GameStatisticsSerializer(serializers.Serializer):
    """Serializer pour les statistiques de jeu."""
    
    def to_representation(self, user):
        """Générer les statistiques de l'utilisateur."""
        from django.db.models import Count, Sum, Avg, Q
        from decimal import Decimal
        
        # Statistiques générales
        total_games = Game.objects.filter(
            Q(player1=user) | Q(player2=user),
            status='finished'
        ).count()
        
        games_won = Game.objects.filter(winner=user).count()
        games_lost = total_games - games_won
        win_rate = (games_won / total_games * 100) if total_games > 0 else 0
        
        # Statistiques financières
        total_bet = Game.objects.filter(
            Q(player1=user) | Q(player2=user),
            status='finished'
        ).aggregate(total=Sum('bet_amount'))['total'] or Decimal('0')
        
        total_winnings = Game.objects.filter(
            winner=user
        ).aggregate(total=Sum('winner_prize'))['total'] or Decimal('0')
        
        # Statistiques par type de jeu
        game_type_stats = []
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
                game_type_stats.append({
                    'game_type': GameTypeSerializer(game_type).data,
                    'games_played': type_games,
                    'games_won': type_wins,
                    'win_rate': round(type_wins / type_games * 100, 2)
                })
        
        # Parties récentes
        recent_games = Game.objects.filter(
            Q(player1=user) | Q(player2=user)
        ).select_related(
            'game_type', 'player1', 'player2', 'winner'
        ).order_by('-finished_at')[:5]
        
        return {
            'total_games': total_games,
            'games_won': games_won,
            'games_lost': games_lost,
            'win_rate': round(win_rate, 2),
            'total_bet': total_bet,
            'total_winnings': total_winnings,
            'profit_loss': total_winnings - total_bet,
            'game_type_statistics': game_type_stats,
            'recent_games': GameListSerializer(recent_games, many=True).data,
            'current_balance': {
                'fcfa': user.get_balance('FCFA'),
                'eur': user.get_balance('EUR'),
                'usd': user.get_balance('USD'),
            }
        }
        
