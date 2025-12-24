# apps/games/models.py
# ====================

import uuid
from decimal import Decimal
from django.db import models
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.core.exceptions import ValidationError
import logging
logger = logging.getLogger(__name__)

class GameType(models.Model):
    """Types de jeux disponibles."""
    
    GAME_CATEGORIES = [
        ('strategy', _('Stratégie')),
        ('cards', _('Cartes')),
        ('board', _('Plateau')),
        ('puzzle', _('Puzzle')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('Nom'), max_length=50, unique=True)
    display_name = models.CharField(_('Nom d\'affichage'), max_length=100)
    description = models.TextField(_('Description'))
    category = models.CharField(_('Catégorie'), max_length=20, choices=GAME_CATEGORIES)
    
    # Configuration du jeu
    min_players = models.PositiveIntegerField(_('Joueurs minimum'), default=2)
    max_players = models.PositiveIntegerField(_('Joueurs maximum'), default=2)
    estimated_duration = models.PositiveIntegerField(_('Durée estimée (minutes)'), default=15)
    
    # Paramètres de mise
    min_bet_fcfa = models.DecimalField(_('Mise minimum FCFA'), max_digits=10, decimal_places=2, default=500)
    max_bet_fcfa = models.DecimalField(_('Mise maximum FCFA'), max_digits=10, decimal_places=2, default=1000000)
    
    # Métadonnées
    is_active = models.BooleanField(_('Actif'), default=True)
    icon = models.ImageField(_('Icône'), upload_to='game_icons/', null=True, blank=True)
    rules_url = models.URLField(_('Lien vers les règles'), blank=True)
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        db_table = 'game_types'
        verbose_name = _('Type de jeu')
        verbose_name_plural = _('Types de jeux')
        ordering = ['display_name']
    
    def __str__(self):
        return self.display_name


class Game(models.Model):
    """Modèle principal pour les parties de jeu."""
    
    GAME_STATUS_CHOICES = [
        ('waiting', _('En attente d\'un joueur')),
        ('ready', _('Prêt à commencer')),
        ('playing', _('En cours')),
        ('paused', _('En pause')),
        ('finished', _('Terminé')),
        ('cancelled', _('Annulé')),
        ('disputed', _('En litige')),
        ('abandoned', _('Abandonné')),
    ]
    
    CURRENCIES = [
        ('FCFA', 'FCFA'),
        ('EUR', 'EUR'),
        ('USD', 'USD'),
    ]
    
    # Identifiants
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    room_code = models.CharField(_('Code de partie'), max_length=8, unique=True, blank=True)
    
    # Configuration du jeu
    game_type = models.ForeignKey(
        GameType,
        on_delete=models.CASCADE,
        related_name='games',
        verbose_name=_('Type de jeu')
    )
    
    # Joueurs
    player1 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='games_as_player1',
        verbose_name=_('Joueur 1')
    )
    player2 = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='games_as_player2',
        verbose_name=_('Joueur 2'),
        null=True,
        blank=True
    )
    current_player = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='current_games',
        verbose_name=_('Joueur actuel'),
        null=True,
        blank=True
    )
    
    # Mise et monnaie
    bet_amount = models.DecimalField(
        _('Montant de la mise'),
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(Decimal('0.01'))]
    )
    currency = models.CharField(_('Devise'), max_length=5, choices=CURRENCIES, default='FCFA')
    total_pot = models.DecimalField(
        _('Cagnotte totale'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    commission = models.DecimalField(
        _('Commission'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    winner_prize = models.DecimalField(
        _('Prix du gagnant'),
        max_digits=10,
        decimal_places=2,
        default=Decimal('0.00')
    )
    
    # État de la partie
    status = models.CharField(
        _('Statut'),
        max_length=20,
        choices=GAME_STATUS_CHOICES,
        default='waiting'
    )
    winner = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='won_games',
        verbose_name=_('Gagnant')
    )
    
    # Données du jeu
    game_data = models.JSONField(_('Données de la partie'), default=dict)
    move_history = models.JSONField(_('Historique des coups'), default=list)
    
    # Gestion du temps
    turn_start_time = models.DateTimeField(_('Début du tour'), null=True, blank=True)
    turn_timeout = models.PositiveIntegerField(_('Timeout du tour (secondes)'), default=120)
    player1_time_left = models.PositiveIntegerField(_('Temps restant J1 (secondes)'), default=21000)  # 5 heures 50 minutes
    player2_time_left = models.PositiveIntegerField(_('Temps restant J2 (secondes)'), default=21000)  # 5 heures 50 minutes
    
    # Métadonnées temporelles
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    started_at = models.DateTimeField(_('Commencé le'), null=True, blank=True)
    finished_at = models.DateTimeField(_('Terminé le'), null=True, blank=True)
    last_move_at = models.DateTimeField(_('Dernier coup le'), null=True, blank=True)
    
    # Paramètres avancés
    is_private = models.BooleanField(_('Partie privée'), default=False)
    is_rated = models.BooleanField(_('Partie classée'), default=True)
    spectators_allowed = models.BooleanField(_('Spectateurs autorisés'), default=True)
    
    class Meta:
        db_table = 'games'
        verbose_name = _('Partie')
        verbose_name_plural = _('Parties')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['player1', 'created_at']),
            models.Index(fields=['player2', 'created_at']),
            models.Index(fields=['room_code']),
            models.Index(fields=['game_type', 'status']),
        ]
    
    def __str__(self):
        return f"{self.game_type.display_name} - {self.room_code}"
    
    def save(self, *args, **kwargs):
        # Générer un code de partie unique
        if not self.room_code:
            self.room_code = self.generate_room_code()
        
        # Calculer les montants financiers
        if self.bet_amount and self.bet_amount > 0:
            self.total_pot = self.bet_amount * 2
            commission_rate = Decimal(str(settings.GAME_SETTINGS.get('COMMISSION_RATE', 0.14)))
            self.commission = self.total_pot * commission_rate
            self.winner_prize = self.total_pot - self.commission
        
        super().save(*args, **kwargs)
    
    def generate_room_code(self):
        """Générer un code de partie unique."""
        import string
        import secrets
        
        while True:
            code = ''.join(secrets.choice(string.ascii_uppercase + string.digits) for _ in range(6))
            if not Game.objects.filter(room_code=code).exists():
                return code
    
    def can_join(self, user):
        """Vérifier si un utilisateur peut rejoindre la partie."""
        if self.status != 'waiting':
            return False, _('La partie n\'est plus en attente de joueurs')
        
        if self.player1 == user:
            return False, _('Vous êtes déjà dans cette partie')
        
        # Vérifier les fonds suffisants
        balance = user.get_balance(self.currency)
        if balance < self.bet_amount:
            return False, _('Solde insuffisant')
        
        # Vérifier le KYC pour les gros montants
        if self.bet_amount >= Decimal('10000') and user.kyc_status != 'approved':
            return False, _('Vérification KYC requise pour cette mise')
        
        return True, _('Peut rejoindre la partie')
    
    def join_game(self, user):
        """Faire rejoindre un utilisateur à la partie."""
        can_join, message = self.can_join(user)
        if not can_join:
            raise ValidationError(message)
        
        # Débiter le montant de la mise
        user.update_balance(self.currency, self.bet_amount, 'subtract')
        
        # Assigner le joueur
        self.player2 = user
        self.status = 'ready'
        # IMPORTANT: Ne pas écraser game_data qui contient les couleurs déjà choisies
        self.save(update_fields=['player2', 'status'])
        
        return True
    
    def start_game(self):
        """Démarrer la partie."""
        import logging
        logger = logging.getLogger("game_start")
        if self.status != 'ready':
            raise ValidationError(_('La partie n\'est pas prête à être démarrée'))
        if not self.player1 or not self.player2:
            raise ValidationError(_('Il manque des joueurs'))
        self.status = 'playing'
        self.started_at = timezone.now()
        self.current_player = self.player1  # Le créateur commence
        self.turn_start_time = timezone.now()
        #self.save()
        logger.info(f"start_game called for game {self.id} type {self.game_type.name}")
        # Initialiser les données de jeu selon le type
        self.initialize_game_data()
        # Correction : forcer l'initialisation des cartes si game_data est vide
        if self.game_type.name == 'Cartes':
            if not self.game_data or not self.game_data.get('player1_hand') or not self.game_data.get('player2_hand'):
                logger.info(f"Force card initialization for game {self.id}")
                self.initialize_cards()
        self.save()
    
    def initialize_game_data(self):
        """Initialiser les données de jeu selon le type."""
        game_logic_map = {
            'chess': self.initialize_chess,
            'Chess': self.initialize_chess,
            'Échecs': self.initialize_chess,  # Support du nom français
            'échecs': self.initialize_chess,  # Support minuscules
            'checkers': self.initialize_checkers,
            'Checkers': self.initialize_checkers,
            'Dames': self.initialize_checkers,  # Support français
            'dames': self.initialize_checkers,
            'Ludo': self.initialize_ludo,  # Corriger la casse
            'ludo': self.initialize_ludo,  # Garde les deux pour compatibilité
            'cards': self.initialize_cards,
            'Cards': self.initialize_cards,
            'Cartes': self.initialize_cards,  # Ajouter aussi la version française
            'cartes': self.initialize_cards,
        }
        
        initializer = game_logic_map.get(self.game_type.name)
        if initializer:
            initializer()
        else:
            # Log pour débugger les types non trouvés
            import logging
            logger = logging.getLogger(__name__)
            logger.warning(f"Aucun initialiseur trouvé pour le type de jeu: '{self.game_type.name}'")
    
    def initialize_chess(self):
        """Initialiser une partie d'échecs COMPÉTITIVE avec timer et système de points."""
        try:
            from apps.games.game_logic.chess_competitive import (
                create_competitive_chess_game,
                convert_chess_board_to_unicode
            )
            
            # Créer une nouvelle partie compétitive
            game_state = create_competitive_chess_game()
            
            # Mapper les joueurs aux couleurs
            game_state['player_mapping'] = {
                'white': str(self.player1.id),
                'black': str(self.player2.id) if self.player2 else None
            }
            
            # Ajouter le board en format Unicode pour le frontend
            game_state['board_unicode'] = convert_chess_board_to_unicode(game_state)
            
            # Stocker l'état complet du jeu
            self.game_data = game_state
            
            # Player1 = blanc, Player2 = noir
            self.current_player = self.player1
            
            logger.info(f"✅ Competitive chess game initialized for game {self.id}")
            self.save()
            
        except Exception as e:
            logger.error(f"Error initializing chess game: {e}")
            raise ValidationError(f"Erreur lors de l'initialisation des échecs: {e}")
    
    def initialize_checkers(self):
        """Initialiser une partie de dames 10x10 compétitives avec timer et système de points."""
        try:
            from apps.games.game_logic.checkers_competitive import (
                create_competitive_checkers_game,
                convert_board_to_unicode
            )
            
            # Créer une nouvelle partie compétitive
            game_state = create_competitive_checkers_game()
            
            # Mapper les joueurs aux couleurs
            game_state['player_mapping'] = {
                'red': str(self.player1.id),
                'black': str(self.player2.id) if self.player2 else None
            }
            
            # Ajouter le board en format Unicode pour le frontend
            game_state['board_unicode'] = convert_board_to_unicode(game_state)
            
            # Stocker l'état complet du jeu
            self.game_data = game_state
            
            # Player1 = rouge (commence), Player2 = noir
            self.current_player = self.player1
            
            logger.info(f"Competitive checkers game initialized for game {self.id}")
            logger.info(f"Red player: {self.player1.username}, Black player: {self.player2.username if self.player2 else 'None'}")
            logger.info(f"Timer: {game_state['timer']['move_time_limit']}s per move, {game_state['timer']['global_time_limit']}s total")
            self.save()
            
        except Exception as e:
            logger.error(f"Error initializing competitive checkers game: {e}")
            raise ValidationError(f"Erreur lors de l'initialisation des dames compétitives: {e}")
    
    def initialize_ludo(self):
        """Initialiser une partie de ludo compétitive avec timer et scoring."""
        from apps.games.game_logic.ludo_competitive import (
            create_competitive_ludo_game,
            LudoTimer,
            LudoScore
        )
        
        # Initialiser game_data si nécessaire
        if not self.game_data:
            self.game_data = {}
        if 'player_colors' not in self.game_data:
            self.game_data['player_colors'] = {}
        
        player_colors = self.game_data['player_colors']
        
        # Player2 doit avoir choisi sa couleur lors du join
        player2_color = player_colors.get(str(self.player2.id)) if self.player2 else None
        
        if not player2_color:
            logger.error(f"Impossible d'initialiser Ludo - Player2 n'a pas choisi de couleur")
            raise ValidationError("Le joueur 2 doit choisir sa couleur avant de démarrer")
        
        # Attribuer automatiquement la couleur opposée à player1
        # Règle: red ↔ yellow, blue ↔ green
        opposite_colors = {
            'red': 'yellow',
            'yellow': 'red',
            'blue': 'green',
            'green': 'blue'
        }
        
        player1_color = opposite_colors.get(player2_color)
        if not player1_color:
            logger.error(f"Couleur invalide pour player2: {player2_color}")
            raise ValidationError(f"Couleur invalide: {player2_color}")
        
        # Sauvegarder la couleur de player1
        player_colors[str(self.player1.id)] = player1_color
        self.game_data['player_colors'] = player_colors
        
        logger.info(f"Attribution automatique: Player1={player1_color}, Player2={player2_color}")
        
        # Utiliser les couleurs réellement choisies par les joueurs
        active_colors = [player1_color, player2_color]
        turn_order = active_colors  # L'ordre de jeu suit l'ordre des couleurs choisies
        
        # Créer uniquement les pièces pour les couleurs actives (tableau plat)
        pieces = []
        for color in active_colors:
            for i in range(4):
                pieces.append({
                    'id': f'{color}-{i}',
                    'color': color,
                    'position': -1,
                    'isInPlay': False
                })
        
        # Le joueur qui commence est le créateur de la partie (player1)
        starting_player_color = player1_color
        
        logger.info(f"Initialisation Ludo compétitif - Couleurs actives: {active_colors}, Premier joueur: {starting_player_color}")
        
        # Créer timer et scores avec les vraies couleurs des joueurs
        timer = LudoTimer(
            turn_order=turn_order,  # Utiliser les vraies couleurs (green, blue, etc.)
            current_player=starting_player_color,
            player_times={color: 21000.0 for color in turn_order}  # Initialiser 5 heures 50 minutes par joueur
        )
        timer.start_game()  # ⏱️ IMPORTANT: Démarrer le chronomètre du jeu !
        logger.info(f"⏰ Timer créé et démarré avec turn_order: {turn_order}, player_times: {list(timer.player_times.keys())}")
        
        # Créer les scores pour les deux couleurs actives
        scores = {}
        for color in active_colors:
            scores[f'{color}_score'] = LudoScore(color=color).to_dict()
        
        self.game_data = {
            'pieces': pieces,
            'current_player': starting_player_color,  # Le créateur commence toujours
            'current_dice_value': 0,
            'can_roll_dice': True,
            'consecutive_sixes': 0,
            'legal_moves': [],
            'status': 'playing',
            'player_colors': player_colors,  # Conserver les couleurs assignées
            'turn_order': turn_order,  # Ordre basé sur les couleurs réelles
            'active_colors': active_colors,  # Seulement les couleurs des joueurs présents
            'timer': timer.to_dict(),
            **scores,  # Ajouter les scores dynamiquement
            'is_game_over': False,
            'winner': None
        }
        # Ne pas écraser current_player dans game_data - il est déjà défini correctement
        self.save()
    
    def initialize_cards(self):
        """Initialiser une partie de cartes avec timer (30 secondes par tour)."""
        import random
        from datetime import datetime, timezone
        
        # Créer et mélanger un jeu de cartes avec le bon format
        suits = [
            ('hearts', '♥️'),
            ('diamonds', '♦️'),
            ('clubs', '♣️'),
            ('spades', '♠️')
        ]
        ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
        
        # Valeurs numériques des cartes
        rank_values = {
            '2': 2, '3': 3, '4': 4, '5': 5, '6': 6, '7': 7, '8': 8, '9': 9, '10': 10,
            'J': 11, 'Q': 12, 'K': 13, 'A': 14
        }
        
        # Créer le deck avec le format frontend
        deck = []
        for suit_name, suit_emoji in suits:
            for rank in ranks:
                card = {
                    'id': f'{suit_emoji}-{rank}',
                    'suit': suit_emoji,
                    'rank': rank,
                    'value': rank_values[rank]
                }
                deck.append(card)
        
        random.shuffle(deck)
        
        # ⏱️ Timer compétitif (30 secondes par tour)
        now = datetime.now(timezone.utc).isoformat()
        timer = {
            'move_time_limit': 120,  # 120 secondes par coup
            'move_time_remaining': 120,
            'current_move_start': now,
            'player1_total_time': 21000,  # 5 heures 50 minutes total par joueur
            'player2_total_time': 21000,
            'game_start_time': now
        }
        
        self.game_data = {
            'deck': deck,
            'player1_hand': deck[:7],
            'player2_hand': deck[7:14],
            'discard_pile': [deck[14]],
            'current_card': deck[14],
            'played_cards': [],  # Cartes actuellement sur la table
            'table_cards': {     # Cartes de chaque joueur pour le tour
                'player1_card': None,
                'player2_card': None
            },
            'round_winner': None,  # Gagnant du tour actuel
            'scores': {'player1': 0, 'player2': 0},
            'total_rounds': 0,
            'timer': timer  # ⏱️ Ajouter le timer
        }
        
        # Player1 commence
        self.current_player = self.player1
        
        self.save()
    
    def get_initial_chess_board(self):
        """Obtenir la position initiale des échecs."""
        return [
            ['r', 'n', 'b', 'q', 'k', 'b', 'n', 'r'],
            ['p', 'p', 'p', 'p', 'p', 'p', 'p', 'p'],
            ['.', '.', '.', '.', '.', '.', '.', '.'],
            ['.', '.', '.', '.', '.', '.', '.', '.'],
            ['.', '.', '.', '.', '.', '.', '.', '.'],
            ['.', '.', '.', '.', '.', '.', '.', '.'],
            ['P', 'P', 'P', 'P', 'P', 'P', 'P', 'P'],
            ['R', 'N', 'B', 'Q', 'K', 'B', 'N', 'R']
        ]
    
    def get_initial_checkers_board(self):
        """Obtenir la position initiale des dames."""
        board = [['.' for _ in range(8)] for _ in range(8)]
        
        # Placer les pièces noires (joueur 1)
        for row in range(3):
            for col in range(8):
                if (row + col) % 2 == 1:
                    board[row][col] = 'b'
        
        # Placer les pièces blanches (joueur 2)
        for row in range(5, 8):
            for col in range(8):
                if (row + col) % 2 == 1:
                    board[row][col] = 'w'
        
        return board
    
    def make_move(self, player, move_data):
        """Effectuer un mouvement dans la partie."""
        logger.info(f"🎲 === MAKE_MOVE MODEL === Player: {player.username}, move_data: {move_data}")
        logger.debug(f"make_move appelé par {player.username} avec move_data: {move_data}")
        
        # Pour Ludo, afficher le current_player couleur; pour autres jeux, afficher l'utilisateur
        game_type_name = getattr(self.game_type, 'name', None)
        game_type_name_lower = game_type_name.lower() if game_type_name else None
        
        if game_type_name_lower == 'ludo':
            ludo_current_player = self.game_data.get('current_player', 'none') if self.game_data else 'none'
            logger.debug(f"Game status: {self.status}, current_player (Ludo color): {ludo_current_player}")
        else:
            logger.debug(f"Game status: {self.status}, current_player: {self.current_player}")
        
        if self.status != 'playing':
            logger.error(f"Game status is '{self.status}', not 'playing'")
            raise ValidationError(_('La partie n\'est pas en cours'))
        
        # ⏱️ Permettre TIMEOUT_CHECK sans vérification du tour
        action = move_data.get('action')
        if action == 'TIMEOUT_CHECK':
            logger.info(f"⏱️ TIMEOUT_CHECK received from {player.username}")
            # Appeler directement le validateur pour vérifier le timeout
            game_type_normalized = game_type_name if game_type_name else None
            if game_type_normalized and game_type_normalized.lower() in ['cards', 'cartes']:
                return self.validate_cards_move(move_data)
            else:
                logger.warning(f"TIMEOUT_CHECK not supported for game type: {game_type_normalized}")
                return True
        
        # Validation des mouvements par type de jeu
        game_type_name = getattr(self.game_type, 'name', None)
        # Normaliser le nom pour la comparaison - utiliser le nom exact
        game_type_normalized = game_type_name if game_type_name else None
        
        validators = {
            'chess': self.validate_chess_move,
            'Chess': self.validate_chess_move,
            'Échecs': self.validate_chess_move,  # Support français
            'échecs': self.validate_chess_move,
            'checkers': self.validate_checkers_move,
            'Checkers': self.validate_checkers_move,
            'Dames': self.validate_checkers_move,  # Support français
            'dames': self.validate_checkers_move,
            'cards': self.validate_cards_move,
            'Cards': self.validate_cards_move,
            'cartes': self.validate_cards_move,  # Support French name
            'Cartes': self.validate_cards_move,
            'ludo': self.validate_ludo_move,
            'Ludo': self.validate_ludo_move,
        }
        
        validator = validators.get(game_type_normalized)
        if not validator:
            logger.error(f"No validator found for game type: {game_type_name} (normalized: {game_type_normalized})")
            raise ValidationError(_('Type de jeu non supporté'))
        
        if not validator(move_data):
            logger.error(f"Move validation failed for {game_type_name}")
            raise ValidationError(_('Mouvement invalide'))
        
        # Processing specific to game type
        if game_type_normalized in ['cards', 'cartes', 'Cards', 'Cartes']:
            action = move_data.get('action')
            if action == 'PLAY_CARD':
                card_data = move_data.get('card')
                if not card_data:
                    raise ValidationError(_('Données de carte manquantes'))
                self.process_card_play(player, card_data)
            elif action == 'DRAW_CARD':
                self.process_draw_card(player)
            elif action == 'PASS_TURN':
                self.switch_turn()
            else:
                raise ValidationError(_(f'Action non supportée: {action}'))
                
        elif game_type_normalized in ['chess', 'Chess', 'Échecs', 'échecs']:
            action = move_data.get('action', 'MOVE_PIECE')
            if action == 'MOVE_PIECE':
                if not self.process_chess_move(player, move_data):
                    raise ValidationError(_('Mouvement d\'échecs invalide'))
            else:
                raise ValidationError(_(f'Action d\'échecs non supportée: {action}'))
                
        elif game_type_normalized in ['ludo', 'Ludo']:
            # ⏱️ Vérifier AVANT toute action si le jeu est déjà terminé par timeout
            from apps.games.game_logic.ludo_competitive import check_competitive_ludo_game_over
            is_over, winner, details = check_competitive_ludo_game_over(self.game_data)
            if is_over and not self.game_data.get('is_game_over'):
                logger.warning(f"⏱️ Game already over by timeout before action, ending game now")
                self.game_data['is_game_over'] = True
                self.game_data['winner'] = winner
                self.game_data['game_over_details'] = details
                
                # Récupérer le joueur gagnant
                winner_player = None
                if winner and winner != 'draw':
                    player_colors = self.game_data.get('player_colors', {})
                    for player_id, color in player_colors.items():
                        if color == winner:
                            winner_player = self.player1 if str(self.player1.id) == player_id else self.player2
                            break
                
                reason = 'timeout' if details.get('reason') == 'global_timeout' else 'victory'
                self.end_game(winner_player if winner != 'draw' else None, reason=reason)
                self.save()
                # Ne pas lever d'erreur, juste retourner True pour que le frontend reçoive le statut
                logger.info("✅ Game ended by timeout, returning success to update frontend")
                return True
            
            action = move_data.get('action')
            if action == 'ROLL_DICE':
                if not self.process_ludo_dice_roll(player):
                    raise ValidationError(_('Impossible de lancer le dé'))
            elif action == 'MOVE_PIECE':
                piece_id = move_data.get('piece_id')
                dice_value = move_data.get('dice_value')
                if piece_id is None or dice_value is None:
                    raise ValidationError(_('Données de mouvement manquantes'))
                if not self.process_ludo_piece_move(player, piece_id, dice_value):
                    raise ValidationError(_('Mouvement de pièce invalide'))
            else:
                raise ValidationError(_(f'Action Ludo non supportée: {action}'))
                
        elif game_type_normalized in ['checkers', 'Checkers', 'Dames', 'dames']:
            action = move_data.get('action', 'MOVE_PIECE')
            if action == 'MOVE_PIECE':
                if not self.process_checkers_move(player, move_data):
                    raise ValidationError(_('Mouvement de dames invalide'))
            else:
                raise ValidationError(_(f'Action de dames non supportée: {action}'))
        
        # Add move to history
        self.move_history.append({
            'player': player.username,
            'move': move_data,
            'timestamp': timezone.now().isoformat(),
            'turn_number': len(self.move_history) + 1
        })

        # Vérifier les conditions de victoire
        winner = None
        if game_type_normalized in ['ludo', 'Ludo']:
            winner = self.check_ludo_win()
        elif game_type_normalized in ['chess', 'Chess', 'Échecs', 'échecs']:
            winner = self.check_chess_win()
        else:
            winner = self.check_win_condition()
            
        if winner:
            self.end_game(winner)
        
        # 🎯 LUDO: Pour Ludo, current_player doit rester la couleur (string), PAS un User object
        # On ne touche PAS à self.current_player car il est géré par le serializer
        if game_type_normalized in ['ludo', 'Ludo']:
            current_color = self.game_data.get('current_player')
            logger.info(f"🎯 Ludo current_player color: {current_color}")
            # Ne PAS modifier self.current_player - il sera lu depuis game_data par le serializer
        
        self.last_move_at = timezone.now()
        self.save()
        logger.info(f"Mouvement accepté pour {player.username}")
        return {
            'success': True,
            'message': 'Mouvement accepté'
        }
        
        if not self.current_player:
            logger.error("current_player is None/NULL - initializing to player1")
            self.current_player = self.player1
            self.turn_start_time = timezone.now()
            self.save()
        
        if self.current_player != player:
            logger.error(f"Not player's turn: current={self.current_player}, trying={player}")
            raise ValidationError(_('Ce n\'est pas votre tour'))
        
        # Vérifier le timeout
        if self.is_turn_timeout():
            self.handle_timeout()
            return False
        
        # Valider et appliquer le mouvement selon le type de jeu
        move_validator_map = {
            'chess': self.validate_chess_move,
            'checkers': self.validate_checkers_move,
            'ludo': self.validate_ludo_move,
            'cards': self.validate_cards_move,
            'Cartes': self.validate_cards_move,  # Support for French name
        }
        
        validator = move_validator_map.get(self.game_type.name)
        if not validator:
            logger.error(f"Aucun validateur pour le type de jeu '{self.game_type.name}'. Types supportés: {list(move_validator_map.keys())}")
            return False
    
        if not validator(move_data):
            logger.info(f"Validation du mouvement échouée pour {player.username} avec {move_data}")
            return {
                'success': False,
                'message': 'Mouvement invalide'
            }

        # Traitement spécial pour les cartes
        if self.game_type.name in ['cards', 'Cartes'] and move_data.get('action') == 'PLAY_CARD':
            card_data = move_data.get('card', {})
            if self.process_card_play(player, card_data):
                logger.info(f"Card play processed for {player.username}")
            else:
                return {
                    'success': False,
                    'message': 'Erreur lors du traitement de la carte'
                }
        else:
            # Appliquer le mouvement standard
            self.switch_turn()
            logger.debug(f"After switch_turn: current_player = {self.current_player}")

        # Sauvegarder l'historique du mouvement
        self.move_history.append({
            'player': player.username,
            'move': move_data,
            'timestamp': timezone.now().isoformat(),
            'turn_number': len(self.move_history) + 1
        })

        # Vérifier les conditions de victoire
        winner = None
        if game_type_name == 'ludo':
            winner = self.check_ludo_win()
        else:
            winner = self.check_win_condition()
            
        if winner:
            self.end_game(winner)
        
        self.last_move_at = timezone.now()
        self.save()
        logger.info(f"Mouvement accepté pour {player.username}")
        return {
            'success': True,
            'message': 'Mouvement accepté'
        }   
         
    def validate_chess_move(self, move_data):
        """Valider un mouvement d'échecs (validation basique uniquement)."""
        logger.debug(f"Validating chess move: {move_data}")
        
        if not isinstance(move_data, dict):
            logger.error(f"move_data is not a dict: {type(move_data)}")
            return False
        
        from_pos = move_data.get('from')
        to_pos = move_data.get('to')
        action = move_data.get('action', 'MOVE_PIECE')
        
        if not from_pos or not to_pos:
            logger.error("Missing from or to position in chess move")
            return False
        
        # Pour les échecs compétitifs, faire une validation basique
        # La vérification du tour est faite dans process_chess_move() avec is_player_turn_chess()
        try:
            # Vérifier que les positions sont valides (format: a1-h8)
            if len(from_pos) != 2 or len(to_pos) != 2:
                logger.error(f"Invalid position format: {from_pos} -> {to_pos}")
                return False
            
            if from_pos[0] not in 'abcdefgh' or to_pos[0] not in 'abcdefgh':
                logger.error(f"Invalid column: {from_pos} -> {to_pos}")
                return False
            
            if from_pos[1] not in '12345678' or to_pos[1] not in '12345678':
                logger.error(f"Invalid row: {from_pos} -> {to_pos}")
                return False
            
            # Vérifier qu'il y a un board
            if not self.game_data or 'board' not in self.game_data:
                logger.error("No board data found")
                return False
            
            # Vérifier qu'il y a une pièce à la position de départ
            from_row, from_col = self.notation_to_indices(from_pos)
            board_data = self.game_data.get('board', [])
            
            if not (0 <= from_row < 8 and 0 <= from_col < 8):
                logger.error(f"Position out of bounds: {from_pos}")
                return False
            
            piece = board_data[from_row][from_col]
            if not piece:
                logger.error(f"No piece at position {from_pos}")
                return False
            
            logger.info(f"Chess move validated successfully: {from_pos} -> {to_pos}")
            return True
            
        except Exception as e:
            logger.error(f"Error validating chess move: {e}")
            return False
    
    def validate_checkers_move(self, move_data):
        """Valider un mouvement de dames 10x10 compétitif."""
        logger.debug(f"Validating competitive checkers move: {move_data}")
        
        from_pos = move_data.get('from')
        to_pos = move_data.get('to')
        
        if not from_pos or not to_pos:
            logger.error("Missing from/to positions in checkers move")
            return False
        
        # ✅ Utiliser le moteur COMPÉTITIF pour validation
        try:
            from apps.games.game_logic.checkers_competitive import CheckersBoard, Position
            
            # Charger l'état du jeu compétitif
            if not self.game_data:
                logger.error("No game_data found for validation")
                return False
            
            board = CheckersBoard.from_dict(self.game_data)
            
            # Convertir les positions (frontend envoie [row, col])
            if isinstance(from_pos, str):
                from_row, from_col = map(int, from_pos.split(','))
            else:
                from_row, from_col = from_pos
            
            if isinstance(to_pos, str):
                to_row, to_col = map(int, to_pos.split(','))
            else:
                to_row, to_col = to_pos
            
            logger.debug(f"Validating move: ({from_row},{from_col}) -> ({to_row},{to_col})")
            
            # Créer les positions
            from_position = Position(from_row, from_col)
            to_position = Position(to_row, to_col)
            
            # Vérifier qu'il y a une pièce à la position de départ
            piece = board.get_piece(from_position)
            if not piece:
                logger.error(f"No piece at position ({from_row},{from_col})")
                return False
            
            logger.debug(f"Found piece at ({from_row},{from_col}): {piece.color.value} {piece.piece_type.value}")
            
            # Obtenir les mouvements possibles pour cette pièce
            possible_moves = board.get_possible_moves(from_position)
            
            logger.debug(f"Possible moves: {[(m.to_pos.row, m.to_pos.col) for m in possible_moves]}")
            
            # Vérifier si le mouvement demandé est dans les mouvements possibles
            is_valid = any(
                move.to_pos.row == to_row and move.to_pos.col == to_col
                for move in possible_moves
            )
            
            if not is_valid:
                logger.error(f"Move ({from_row},{from_col}) -> ({to_row},{to_col}) not in possible moves")
                return False
            
            logger.info(f"✅ Competitive checkers move validated: ({from_row},{from_col}) -> ({to_row},{to_col})")
            return True
            
        except Exception as e:
            logger.error(f"Error validating checkers move: {e}")
            return False
    
    def validate_ludo_move(self, move_data):
        """Valider un mouvement de ludo."""
        logger.debug(f"Validating ludo move: {move_data}")
        
        if not isinstance(move_data, dict):
            logger.error(f"move_data is not a dict: {type(move_data)}")
            return False
            
        action = move_data.get('action')
        if not action:
            logger.error("No action in move_data")
            return False
            
        valid_actions = ['ROLL_DICE', 'MOVE_PIECE']
        if action not in valid_actions:
            logger.error(f"Invalid action: {action}. Valid actions: {valid_actions}")
            return False
            
        if action == 'MOVE_PIECE':
            piece_id = move_data.get('piece_id')
            dice_value = move_data.get('dice_value')
            if piece_id is None:
                logger.error("MOVE_PIECE action missing piece_id")
                return False
            
            # Validate piece_id format: should be "color-number" (e.g., "blue-0", "red-3")
            if not isinstance(piece_id, str):
                logger.error(f"Invalid piece_id type: {type(piece_id)} - expected string")
                return False
            
            # Check format: color-number
            if '-' not in piece_id:
                logger.error(f"Invalid piece_id format: {piece_id} - expected 'color-number'")
                return False
            
            parts = piece_id.split('-')
            if len(parts) != 2:
                logger.error(f"Invalid piece_id format: {piece_id} - expected 'color-number'")
                return False
            
            color, number_str = parts
            valid_colors = ['red', 'blue', 'green', 'yellow']
            if color not in valid_colors:
                logger.error(f"Invalid color in piece_id: {color} - valid colors: {valid_colors}")
                return False
            
            try:
                piece_number = int(number_str)
                if piece_number < 0 or piece_number > 3:
                    logger.error(f"Invalid piece number in piece_id: {piece_number} - must be 0-3")
                    return False
            except ValueError:
                logger.error(f"Invalid piece number in piece_id: {number_str} - must be integer")
                return False
            
            # dice_value validation is optional for MOVE_PIECE (can be 0 if already rolled)
            if dice_value is not None and (not isinstance(dice_value, int) or dice_value < 0 or dice_value > 6):
                logger.error(f"Invalid dice_value: {dice_value}")
                return False
        
        logger.info(f"Ludo move validated successfully: {action}")
        return True
    
    def validate_cards_move(self, move_data):
        """Valider un mouvement de cartes avec mise à jour du timer."""
        from datetime import datetime, timezone
        
        logger.debug(f"Validating cards move: {move_data}")
        
        if not isinstance(move_data, dict):
            logger.error(f"move_data is not a dict: {type(move_data)}")
            return False
            
        action = move_data.get('action')
        if not action:
            logger.error("No action in move_data")
            return False
            
        # Valider les actions supportées
        valid_actions = ['DRAW_CARD', 'PLAY_CARD', 'PASS_TURN', 'TIMEOUT_CHECK']
        if action not in valid_actions:
            logger.error(f"Invalid action: {action}. Valid actions: {valid_actions}")
            return False
        
        # ⏱️ Vérifier le timeout AVANT de valider le coup
        timer = self.game_data.get('timer', {})
        if timer:
            current_move_start = timer.get('current_move_start')
            if current_move_start:
                try:
                    move_start = datetime.fromisoformat(current_move_start.replace('Z', '+00:00'))
                    now = datetime.now(timezone.utc)
                    elapsed = (now - move_start).total_seconds()
                    
                    # Si le temps écoulé dépasse 120 secondes, le joueur actuel perd par timeout
                    if elapsed > 120:
                    
                        logger.warning(f"⏱️ TIMEOUT! {self.current_player.username} took {elapsed:.1f}s (limit: 120s)")
                        logger.info(f"........................................: {self.current_player}")
                        # Déterminer le gagnant (l'adversaire)
                        winner = self.player2 if self.current_player == self.player1 else self.player1
                        
                        # Terminer le jeu avec victoire par timeout
                        self.end_game(winner, reason='timeout')
                        logger.info(f"🏁 GAME OVER: {winner.username} wins by timeout!")
                        
                        return False
                except Exception as e:
                    logger.warning(f"Error checking timeout: {e}")
        
        # Si c'est juste une vérification de timeout, on arrête ici
        if action == 'TIMEOUT_CHECK':
            logger.info("TIMEOUT_CHECK action - no timeout detected")
            return True
            
        # Validation spécifique par action
        if action == 'PLAY_CARD':
            if 'card' not in move_data:
                logger.error("PLAY_CARD action missing 'card' data")
                return False
        
        # ⏱️ Mettre à jour le timer après un coup valide
        if action in ['PLAY_CARD', 'PASS_TURN']:
            if timer:
                # Calculer le temps écoulé depuis le début du coup
                current_move_start = timer.get('current_move_start')
                if current_move_start:
                    try:
                        move_start = datetime.fromisoformat(current_move_start.replace('Z', '+00:00'))
                        now = datetime.now(timezone.utc)
                        elapsed = (now - move_start).total_seconds()
                        
                        # Déduire le temps du joueur actuel
                        if self.current_player == self.player1:
                            timer['player1_total_time'] = max(0, timer.get('player1_total_time', 21000) - elapsed)
                        else:
                            timer['player2_total_time'] = max(0, timer.get('player2_total_time', 00) - elapsed)
                    except Exception as e:
                        logger.warning(f"Error calculating timer: {e}")
                
                # Réinitialiser le timer pour le prochain coup
                now = datetime.now(timezone.utc).isoformat()
                timer['current_move_start'] = now
                timer['move_time_remaining'] = 120  # Reset to 120 seconds
                
                self.game_data['timer'] = timer
        
        logger.info(f"Cards move validated successfully: {action}")
        return True
    
    def process_ludo_dice_roll(self, player):
        """Traiter le lancer de dé pour Ludo selon les vraies règles."""
        import random
        
        # Vérifier que c'est le tour du joueur
        player_colors = self.game_data.get('player_colors', {})
        player_color = player_colors.get(str(player.id))
        current_player = self.game_data.get('current_player')
        
        # Si current_player n'est pas défini, l'initialiser avec la couleur du premier joueur
        if current_player is None:
            # Déterminer la couleur du créateur (player1)
            creator_color = player_colors.get(str(self.player1.id))
            if creator_color:
                self.game_data['current_player'] = creator_color
                current_player = creator_color
                logger.info(f"Initialized current_player to {current_player}")
            else:
                # Fallback au premier de l'ordre de tour (utiliser active_colors, pas red/blue par défaut)
                active_colors = self.game_data.get('active_colors', self.game_data.get('turn_order', ['red', 'blue']))
                turn_order = self.game_data.get('turn_order', active_colors)
                self.game_data['current_player'] = turn_order[0]
                current_player = turn_order[0]
                logger.info(f"Initialized current_player to {current_player} (fallback from turn_order: {turn_order})")
            self.save()
        
        if player_color != current_player:
            logger.error(f"Not player's turn to roll dice: {player_color} vs {current_player}")
            return False
            
        if not self.game_data.get('can_roll_dice', True):
            logger.error("Player cannot roll dice at this time")
            return False
        
        logger.info(f"🎲 === DICE ROLL START === Player: {player.username}, Color: {player_color}")
        
        # Lancer le dé
        dice_value = random.randint(1, 6)
        self.game_data['current_dice_value'] = dice_value
        self.game_data['can_roll_dice'] = False
        
        logger.info(f"🎲 ROLLED: {dice_value} by {player.username} ({player_color})")
        
        # Gérer les 6 consécutifs (règle Ludo)
        if dice_value == 6:
            consecutive_sixes = self.game_data.get('consecutive_sixes', 0) + 1
            self.game_data['consecutive_sixes'] = consecutive_sixes
            
            # Après 3 six consécutifs, perdre le tour
            if consecutive_sixes >= 3:
                logger.info(f"3 consecutive sixes! {player.username} loses turn")
                self.game_data['consecutive_sixes'] = 0
                self.game_data['can_roll_dice'] = True
                self.game_data['current_dice_value'] = 0
                self.switch_turn_ludo()
                return True
        else:
            self.game_data['consecutive_sixes'] = 0
        
        # Calculer les mouvements légaux
        legal_moves = self.calculate_legal_moves(player_color, dice_value)
        logger.info(f"🎲 Calculated legal moves: {len(legal_moves)} moves")
        
        # Si aucun mouvement possible
        if not legal_moves:
            logger.info(f"🚫 NO LEGAL MOVES for {player.username} (rolled {dice_value})")
            
            # RÈGLE LUDO: Si c'est un 6, le joueur peut relancer
            if dice_value == 6 and self.game_data.get('consecutive_sixes', 0) < 3:
                self.game_data['can_roll_dice'] = True
                logger.info(f"🎲 Rolled 6 but no moves, {player.username} can roll again (stays in turn)")
                # On ne change PAS de joueur, il reste dans son tour
            else:
                # Aucun mouvement et pas de 6 = fin du tour
                logger.info(f"⏭️ PASSING TURN: No moves and dice={dice_value} (not 6)")
                self.game_data['can_roll_dice'] = True
                self.game_data['consecutive_sixes'] = 0
                self.game_data['current_dice_value'] = 0
                self.game_data['legal_moves'] = []
                
                # Mettre à jour le timer et passer au joueur suivant
                from apps.games.game_logic.ludo_competitive import LudoTimer
                timer = LudoTimer.from_dict(self.game_data.get('timer', {}))
                timer.update()  # ⏱️ Mettre à jour le temps écoulé
                timer.switch_player()
                self.game_data['timer'] = timer.to_dict()
                
                old_player = self.game_data['current_player']
                self.switch_turn_ludo()
                new_player = self.game_data['current_player']
                logger.info(f"✅ TURN PASSED: {old_player} → {new_player}")
                
                # Vérifier fin de partie après le changement de tour
                from apps.games.game_logic.ludo_competitive import check_competitive_ludo_game_over
                is_over, winner, details = check_competitive_ludo_game_over(self.game_data)
                if is_over:
                    self.game_data['is_game_over'] = True
                    self.game_data['winner'] = winner
                    self.game_data['game_over_details'] = details
                    
                    # Récupérer le joueur correspondant à la couleur gagnante
                    winner_player = None
                    if winner and winner != 'draw':
                        player_colors = self.game_data.get('player_colors', {})
                        for player_id, color in player_colors.items():
                            if color == winner:
                                winner_player = self.player1 if str(self.player1.id) == player_id else self.player2
                                break
                    
                    if winner == 'draw':
                        self.end_game(None, reason='draw')
                    else:
                        self.end_game(winner_player, reason='timeout')
                    
                    logger.info(f"🏁 GAME OVER: {winner} wins by timeout!")
        else:
            # Il y a des mouvements possibles, le joueur doit jouer
            logger.info(f"✅ LEGAL MOVES AVAILABLE ({len(legal_moves)}): {[m['piece_id'] for m in legal_moves]}")
        
        # Sauvegarder l'état avec legal_moves
        self.save(update_fields=['game_data'])
        return True
    
    def process_ludo_piece_move(self, player, piece_id, dice_value):
        """Traiter le déplacement d'un pion Ludo."""
        player_colors = self.game_data.get('player_colors', {})
        player_color = player_colors.get(str(player.id))
        current_player = self.game_data.get('current_player')
        
        if player_color != current_player:
            logger.error(f"Not player's turn to move: {player_color} vs {current_player}")
            return False
        
        # Vérifier que le dé a la bonne valeur
        if dice_value != self.game_data.get('current_dice_value', 0):
            logger.error(f"Dice value mismatch: {dice_value} vs {self.game_data.get('current_dice_value')}")
            return False
        
        # Vérifier que le mouvement est légal
        legal_moves = self.game_data.get('legal_moves', [])
        if not any(move.get('piece_id') == piece_id for move in legal_moves):
            logger.error(f"Illegal move: piece {piece_id} not in legal moves {legal_moves}")
            return False
        
        # Effectuer le mouvement - trouver le pion par son ID
        pieces = self.game_data.get('pieces', [])
        piece = None
        for p in pieces:
            if p.get('id') == piece_id:
                piece = p
                break
        
        if not piece:
            logger.error(f"Invalid piece_id: {piece_id}")
            return False
        old_position = piece['position']
        
        # Importer le système de scoring
        from apps.games.game_logic.ludo_competitive import (
            LudoScore,
            update_score_for_action,
            LudoTimer,
            check_competitive_ludo_game_over
        )
        
        # Calculer la nouvelle position
        new_position = self.calculate_new_position(player_color, old_position, dice_value)
        
        # ⚠️ VÉRIFIER LES MURS: Si on traverse un portail avec un mur, vérifier si on peut le casser
        # Parcourir le chemin du mouvement
        path_blocked = False
        for step in range(1, dice_value + 1):
            intermediate_pos = old_position + step
            if intermediate_pos >= 52:
                break  # Zone finale
            
            # Vérifier si cette position intermédiaire est un mur
            portal_positions = {0: 'red', 13: 'green', 26: 'yellow', 39: 'blue'}
            if intermediate_pos in portal_positions:
                wall_color = portal_positions[intermediate_pos]
                if wall_color != player_color and self.is_wall_position(intermediate_pos, wall_color):
                    # Il y a un mur! Vérifier si on peut le casser
                    if not self.can_break_wall(player_color, intermediate_pos, dice_value, old_position):
                        path_blocked = True
                        logger.warning(f"🚧 Movement BLOCKED by {wall_color} wall at position {intermediate_pos}")
                        break
        
        if path_blocked:
            # Le mouvement est bloqué par un mur, annuler
            logger.info(f"❌ Movement cancelled - blocked by wall")
            # Le pion reste à sa position
            return False
        
        piece['position'] = new_position
        
        # Récupérer le score du joueur
        score_key = f'{player_color}_score'
        score = LudoScore.from_dict(self.game_data.get(score_key, {}))
        
        # Mise à jour du score selon les actions
        if old_position == -1 and new_position >= 0:
            # Sortir une pièce de la base
            update_score_for_action(score, 'piece_out')
            piece['isInPlay'] = True
            logger.info(f"💎 {player_color} piece out: +{2} pts")
        
        if new_position >= 0:
            piece['isInPlay'] = True
            # Points pour les cases parcourues
            update_score_for_action(score, 'step', dice_value)
        
        # Vérifier si la pièce est arrivée (position 58 = centre)
        if new_position == 58:
            update_score_for_action(score, 'piece_finished')
            logger.info(f"🏆 {player_color} piece finished: +{10} pts")
        
        # Vérifier les captures
        captured = self.check_captures(player_color, new_position)
        if captured > 0:
            update_score_for_action(score, 'piece_captured', captured)
            logger.info(f"⚔️ {player_color} captured {captured} pieces: +{5 * captured} pts")
        
        # Sauvegarder le score mis à jour
        self.game_data[score_key] = score.to_dict()
        
        # Vider les mouvements légaux (ils seront recalculés au prochain lancer)
        self.game_data['legal_moves'] = []
        
        # Mettre à jour le timer
        timer = LudoTimer.from_dict(self.game_data.get('timer', {}))
        timer.update()  # ⏱️ IMPORTANT: Mettre à jour le temps écoulé
        
        # 🎯 RÈGLE LUDO CLASSIQUE: Le joueur rejoue SEULEMENT si:
        # 1. Il a fait un 6 (et pas 3 consécutifs)
        # La capture ne fait PAS rejouer dans Ludo classique
        
        can_roll_again = False
        
        # 📝 Tracker les six consécutifs pour la règle du mur
        if dice_value == 6:
            consecutive = self.game_data.get('consecutive_sixes', 0)
            if consecutive < 3:
                can_roll_again = True
                logger.info(f"🎲 Player {player.username} rolled 6 ({consecutive + 1} consecutive) - can roll again")
        else:
            # Reset le compteur si pas un 6
            self.game_data['consecutive_sixes_history'] = []
        
        if can_roll_again:
            # Le joueur peut lancer à nouveau dans SON tour
            self.game_data['can_roll_dice'] = True
            # Garder current_dice_value pour que le frontend puisse voir le 6
            # Il sera réinitialisé au prochain lancer dans process_ludo_dice_roll()
            # On ne change PAS de joueur - il garde son tour
            # On ne reset PAS consecutive_sixes - il continue à compter
            # On ne reset PAS le timer (même tour continue)
            logger.info(f"✨ {player.username} keeps turn after rolling 6 and moving piece, can roll again")
        else:
            # Fin du tour, passer au joueur suivant
            self.game_data['can_roll_dice'] = True
            self.game_data['consecutive_sixes'] = 0
            self.game_data['current_dice_value'] = 0  # Reset dice value seulement quand le tour change
            
            # Changer de tour et reset timer
            timer.switch_player()
            self.game_data['timer'] = timer.to_dict()
            
            # Passer au joueur suivant
            old_player = self.game_data['current_player']
            self.switch_turn_ludo()
            new_player = self.game_data['current_player']
            logger.info(f"⏭️ Turn ended - switched from {old_player} to {new_player}")
        
        # Vérifier fin de partie
        is_over, winner, details = check_competitive_ludo_game_over(self.game_data)
        logger.info(f"🏁 Game over check: is_over={is_over}, winner={winner}, details={details}")
        if is_over:
            self.game_data['is_game_over'] = True
            self.game_data['winner'] = winner
            self.game_data['game_over_details'] = details
            logger.info(f"🎮 Game ending - winner color: {winner}")
            
            # Terminer le jeu et distribuer les prix
            # Récupérer le joueur correspondant à la couleur gagnante
            winner_player = None
            if winner and winner != 'draw':
                player_colors = self.game_data.get('player_colors', {})
                logger.info(f"🎨 Player colors mapping: {player_colors}")
                for player_id, color in player_colors.items():
                    logger.info(f"  Checking: player_id={player_id}, color={color}, winner={winner}")
                    if color == winner:
                        winner_player = self.player1 if str(self.player1.id) == player_id else self.player2
                        logger.info(f"✅ Winner player found: {winner_player.username}")
                        break
            
            if winner == 'draw':
                self.end_game(None, reason='draw')
            else:
                # Déterminer la raison de la victoire
                reason = 'timeout' if details.get('reason') == 'global_timeout' else 'victory'
                self.end_game(winner_player, reason=reason)
        
        logger.info(f"Piece {piece_id} moved from {old_position} to {new_position}")
        return True
    
    def is_position_blocked(self, position, moving_color):
        """Vérifier si une position est bloquée par 2 pions de même couleur adverse."""
        if position < 0 or position >= 52:  # Pas de blocage en zone finale
            return False
        
        pieces = self.game_data.get('pieces', [])
        pieces_at_position = []
        
        # Compter les pions sur cette position
        for piece in pieces:
            if piece.get('position') == position:
                pieces_at_position.append(piece)
        
        # Si 2 pions ou plus de la MÊME couleur (et pas la nôtre) occupent la case
        if len(pieces_at_position) >= 2:
            first_color = pieces_at_position[0].get('color')
            # Vérifier que tous les pions sont de la même couleur et pas la nôtre
            if all(p.get('color') == first_color for p in pieces_at_position) and first_color != moving_color:
                logger.info(f"🚫 Position {position} is blocked by {first_color} pieces")
                return True
        
        return False
    
    def calculate_legal_moves(self, player_color, dice_value):
        """Calculer les mouvements légaux pour un joueur selon les vraies règles Ludo."""
        legal_moves = []
        pieces = self.game_data.get('pieces', [])
        
        logger.info(f"🔍 calculate_legal_moves: color={player_color}, dice={dice_value}, total_pieces={len(pieces)}")
        
        for piece in pieces:
            # Filtrer seulement les pions de la couleur du joueur
            if piece.get('color') != player_color:
                continue
                
            piece_id = piece.get('id')  # Format: "blue-0", "red-1", etc.
            current_pos = piece['position']
            
            logger.info(f"🎯 Checking piece {piece_id}: position={current_pos}")
            
            # Sortir de la maison seulement avec un 6
            if current_pos == -1:
                if dice_value == 6:
                    start_pos = self.calculate_new_position(player_color, -1, 6)
                    logger.info(f"🏠 Piece {piece_id} can exit to position {start_pos}")
                    # Vérifier que la case de départ n'est pas bloquée
                    if not self.is_position_blocked(start_pos, player_color):
                        legal_moves.append({'piece_id': piece_id, 'from': -1, 'to': start_pos})
                        logger.info(f"✅ Added legal move: {piece_id} from -1 to {start_pos}")
                    else:
                        logger.info(f"🚫 Start position {start_pos} is blocked")
                else:
                    logger.info(f"⛔ Piece {piece_id} in house but dice={dice_value} (need 6)")
                continue
            
            # Mouvement sur le plateau extérieur (0-51)
            if current_pos >= 0 and current_pos < 52:
                new_pos = self.calculate_new_position(player_color, current_pos, dice_value)
                # Vérifier que le mouvement est valide ET que la destination n'est pas bloquée
                if new_pos != current_pos and not self.is_position_blocked(new_pos, player_color):
                    # ⚠️ Vérifier aussi qu'il n'y a pas de mur qui bloque le chemin
                    path_clear = True
                    for step in range(1, dice_value + 1):
                        intermediate_pos = current_pos + step
                        if intermediate_pos >= 52:
                            break
                        
                        # Vérifier si c'est un mur
                        portal_positions = {0: 'red', 13: 'green', 26: 'yellow', 39: 'blue'}
                        if intermediate_pos in portal_positions:
                            wall_color = portal_positions[intermediate_pos]
                            if wall_color != player_color and self.is_wall_position(intermediate_pos, wall_color):
                                # Mur détecté! Vérifier si on peut le casser
                                if not self.can_break_wall(player_color, intermediate_pos, dice_value, current_pos):
                                    path_clear = False
                                    logger.info(f"🚧 Move blocked: {piece_id} cannot pass {wall_color} wall at {intermediate_pos}")
                                    break
                    
                    if path_clear:
                        legal_moves.append({'piece_id': piece_id, 'from': current_pos, 'to': new_pos})
            
            # Mouvement dans la zone finale (52-57)
            elif current_pos >= 52 and current_pos < 58:
                new_pos = current_pos + dice_value
                if new_pos <= 58:  # Ne peut pas dépasser le centre
                    legal_moves.append({'piece_id': piece_id, 'from': current_pos, 'to': new_pos})
        
        self.game_data['legal_moves'] = legal_moves
        logger.info(f"Legal moves for {player_color}: {legal_moves}")
        return legal_moves
    
    def calculate_new_position(self, color, current_pos, dice_value):
        """Calculer la nouvelle position d'un pion selon les vraies règles Ludo."""
        # Positions de départ pour chaque couleur sur le plateau extérieur (52 cases)
        start_positions = {'red': 0, 'green': 13, 'yellow': 26, 'blue': 39}
        
        if current_pos == -1:  # Sortir de la maison avec un 6
            if dice_value == 6:
                return start_positions[color]
            else:
                return -1  # Ne peut pas sortir sans un 6
        
        # Mouvement normal sur le plateau extérieur (52 cases)
        if current_pos >= 0 and current_pos < 52:
            new_pos = current_pos + dice_value
            
            # Vérifier si le pion fait le tour complet et doit entrer dans sa zone finale
            start_pos = start_positions[color]
            
            # Calculer combien de cases le pion a parcouru depuis sa sortie
            if current_pos >= start_pos:
                distance_travelled = current_pos - start_pos
            else:
                # Le pion a fait le tour
                distance_travelled = (52 - start_pos) + current_pos
            
            total_distance = distance_travelled + dice_value
            
            # Si le pion a parcouru 51 cases ou plus, il entre dans sa zone finale
            if total_distance >= 51:
                # Entrée dans la zone finale
                steps_in_final = total_distance - 51
                if steps_in_final <= 6:  # Maximum 6 cases dans la zone finale + centre
                    return 52 + steps_in_final
                else:
                    # Dépassement - mouvement invalide
                    return current_pos  # Reste à la position actuelle
            
            # Mouvement normal sur le plateau
            if new_pos >= 52:
                new_pos = new_pos - 52  # Faire le tour
            
            return new_pos
        
        # Mouvement dans la zone finale (positions 52-58)
        if current_pos >= 52 and current_pos < 58:
            new_pos = current_pos + dice_value
            if new_pos <= 58:  # Position 58 = centre final
                return new_pos
            else:
                # Dépassement interdit en Ludo - le mouvement est invalide
                return current_pos  # Reste à la position actuelle
        
        return current_pos
    
    def is_wall_position(self, position, color):
        """Vérifier si une position contient un mur (2 pions de même couleur au portail)."""
        # Positions de portail (sortie maison)
        portal_positions = {
            0: 'red',
            13: 'green',
            26: 'yellow',
            39: 'blue'
        }
        
        # Vérifier si c'est un portail
        if position not in portal_positions:
            return False
        
        # Compter les pions de cette couleur sur ce portail
        pieces = self.game_data.get('pieces', [])
        count = sum(1 for p in pieces 
                   if p.get('color') == color 
                   and p.get('position') == position 
                   and p.get('isInPlay', False))
        
        return count >= 2
    
    def can_break_wall(self, moving_color, target_position, dice_value, current_position):
        """Vérifier si un joueur peut casser un mur.
        
        Pour casser un mur (2 pions alignés au portail):
        1. Il faut avoir fait 2 six consécutifs dans ce tour
        2. Le dé actuel doit faire tomber EXACTEMENT sur la case du mur
        """
        # Vérifier si la cible est un mur
        portal_positions = {0: 'red', 13: 'green', 26: 'yellow', 39: 'blue'}
        if target_position not in portal_positions:
            return True  # Pas un mur, passage libre
        
        wall_color = portal_positions[target_position]
        if not self.is_wall_position(target_position, wall_color):
            return True  # Pas de mur, passage libre
        
        # C'est un mur! Vérifier les conditions pour le casser
        consecutive_sixes = self.game_data.get('consecutive_sixes', 0)
        
        # Vérifier si on tombe EXACTEMENT sur le mur
        lands_exactly = (current_position + dice_value == target_position)
        
        # Pour casser: besoin de 2 six consécutifs ET tomber exactement dessus
        if consecutive_sixes >= 2 and lands_exactly:
            logger.info(f"💥 WALL BREAK! {moving_color} breaks {wall_color} wall at {target_position} with {consecutive_sixes} consecutive sixes")
            return True
        
        # Sinon, le mur bloque
        if not lands_exactly:
            logger.info(f"🚧 WALL BLOCKS! {wall_color} wall at {target_position} blocks passage (not landing exactly)")
        else:
            logger.info(f"🚧 WALL BLOCKS! {wall_color} wall at {target_position} blocks - need 2 consecutive sixes (have {consecutive_sixes})")
        return False
    
    def check_captures(self, moving_color, position):
        """Vérifier et effectuer les captures selon les nouvelles règles Ludo. 
        
        NOUVELLES RÈGLES:
        1. Capture en avant ET en arrière (position exacte)
        2. Les pions capturés vont à la BASE de celui qui a capturé (pas à leur propre base)
        3. Plusieurs pions de même couleur sur une case = tous capturés ensemble
        4. Les murs au portail (2 pions) NE peuvent PAS être capturés (sauf si cassés)
        
        Retourne le nombre de pièces capturées.
        """
        if position < 0 or position >= 52:  # Pas de capture en zone finale ou maison
            return 0
        
        captured_count = 0
        
        # Positions de sécurité où les pions ne peuvent JAMAIS être capturés
        safe_positions = {
            10,  # Avant entrée couloir rouge
            23,  # Avant entrée couloir vert
            36,  # Avant entrée couloir jaune
            49   # Avant entrée couloir bleu
        }
        
        # Pas de capture sur les positions de sécurité (hors portails)
        if position in safe_positions:
            logger.info(f"🛡️ Position {position} is a safe spot - no capture possible")
            return 0
        
        pieces = self.game_data.get('pieces', [])
        
        # Vérifier si c'est un mur au portail (portail = sortie maison)
        portal_positions = {0: 'red', 13: 'green', 26: 'yellow', 39: 'blue'}
        if position in portal_positions:
            wall_color = portal_positions[position]
            if self.is_wall_position(position, wall_color):
                logger.info(f"🚧 Position {position} has a {wall_color} WALL (2+ pieces) - cannot be captured!")
                return 0  # Les murs ne peuvent pas être capturés
        
        # ✅ NOUVELLE RÈGLE: Capturer TOUS les pions adverses sur cette position
        # (en avant ou en arrière, peu importe)
        # Les pions capturés vont à la BASE de celui qui capture
        for piece in pieces:
            piece_color = piece.get('color')
            if piece_color == moving_color:  # Ne pas capturer ses propres pièces
                continue
            
            # Vérifier si le pion adverse est EXACTEMENT sur la même position
            if piece['position'] == position and piece.get('isInPlay', False):
                # ⚡ NOUVELLE RÈGLE IMPLÉMENTÉE: Le pion capturé va à la BASE de celui qui a capturé
                # Le pion est maintenant "prisonnier" chez l'adversaire
                # Il conserve sa couleur d'origine MAIS est stocké dans la base de moving_color
                
                piece['position'] = -1  # Retour à la base
                piece['isInPlay'] = False
                piece['captured_by'] = moving_color  # ✅ NOUVEAU: Indique dans quelle base il est prisonnier
                
                captured_count += 1
                logger.info(f"⚔️ CAPTURE! {moving_color} captures {piece_color} piece {piece.get('id')} at position {position}")
                logger.info(f"   → Pion {piece_color} envoyé à la BASE de {moving_color} (captured_by={moving_color})")
        
        return captured_count
    
    def switch_turn_ludo(self):
        """Changer de tour pour Ludo en utilisant les couleurs réellement choisies."""
        # Construire l'ordre de tour basé sur les couleurs des joueurs réels
        player_colors = self.game_data.get('player_colors', {})
        active_colors = []
        
        # Ajouter la couleur du player1 d'abord (créateur commence)
        if self.player1 and str(self.player1.id) in player_colors:
            active_colors.append(player_colors[str(self.player1.id)])
        
        # Ajouter la couleur du player2
        if self.player2 and str(self.player2.id) in player_colors:
            active_colors.append(player_colors[str(self.player2.id)])
        
        # Fallback: utiliser SEULEMENT les couleurs déjà dans game_data (turn_order ou active_colors)
        # Ne JAMAIS utiliser ['red', 'blue'] par défaut
        if not active_colors:
            active_colors = self.game_data.get('turn_order') or self.game_data.get('active_colors', [])
            if not active_colors:
                logger.error(f"❌ ERREUR CRITIQUE: Aucune couleur active trouvée! player_colors={player_colors}")
                # En dernier recours, extraire les couleurs depuis player_colors
                active_colors = list(player_colors.values()) if player_colors else []
            logger.warning(f"⚠️ Using fallback colors from game_data: {active_colors}")
        
        current = self.game_data.get('current_player')
        
        if current in active_colors:
            current_index = active_colors.index(current)
            next_index = (current_index + 1) % len(active_colors)
            self.game_data['current_player'] = active_colors[next_index]
        else:
            self.game_data['current_player'] = active_colors[0]
        
        # Réinitialiser les données du tour
        self.game_data['current_dice_value'] = 0
        self.game_data['legal_moves'] = []
        self.game_data['consecutive_sixes'] = 0
        
        logger.info(f"Turn switched to {self.game_data['current_player']}")
    
    def process_card_play(self, user, card_data):
        """Traiter la pose d'une carte selon les règles traditionnelles."""
        logger.info(f"Processing card play for user {user.username}: {card_data}")
        
        # Migrer les anciennes données si nécessaire
        if 'table_cards' not in self.game_data:
            logger.info("Migrating old game data to new format")
            self.game_data.update({
                'table_cards': {
                    'player1_card': None,
                    'player2_card': None
                },
                'round_winner': None,
                'scores': {'player1': 0, 'player2': 0},
                'total_rounds': 0
            })
            self.save()
        
        # Déterminer quel joueur joue
        player_key = 'player1' if user == self.player1 else 'player2'
        opponent_key = 'player1' if player_key == 'player2' else 'player2'
        
        # Ajouter la carte à la table
        self.game_data['table_cards'][f'{player_key}_card'] = card_data
        
        # Retirer la carte de la main du joueur (si les mains existent)
        hand_key = f'{player_key}_hand'
        if hand_key in self.game_data:
            player_hand = self.game_data[hand_key]
            self.game_data[hand_key] = [
                card for card in player_hand 
                if not (card['suit'] == card_data['suit'] and card['rank'] == card_data['rank'])
            ]
        
        # Vérifier si les deux joueurs ont joué
        player1_card = self.game_data['table_cards']['player1_card']
        player2_card = self.game_data['table_cards']['player2_card']
        
        if player1_card and player2_card:
            # Les deux cartes sont posées, déterminer le gagnant
            winner_key = self.determine_round_winner(player1_card, player2_card)
            logger.info(f"Round complete. Winner: {winner_key}")
            
            # Déterminer le nom du joueur gagnant pour le log
            winner_name = self.player1.username if winner_key == 'player1' else self.player2.username
            logger.info(f"Round winner: {winner_name} ({winner_key})")
            
            # Marquer le gagnant du tour
            self.game_data['round_winner'] = winner_key
            self.game_data['total_rounds'] += 1
            
            # Donner un point au gagnant uniquement
            self.game_data['scores']['player1'] = int(self.game_data['scores']['player1'])
            self.game_data['scores']['player2'] = int(self.game_data['scores']['player2'])
            self.game_data['scores'][winner_key] += 1
            logger.info(f"Updated scores: {self.game_data['scores']}")
            
            # Le gagnant commence le prochain tour
            if winner_key == 'player1':
                self.current_player = self.player1
            else:
                self.current_player = self.player2
            logger.info(f"Next turn: {self.current_player.username} starts")
            
            # Nettoyer la table immédiatement
            self.game_data['table_cards'] = {
                'player1_card': None,
                'player2_card': None
            }
            self.game_data['round_winner'] = None
            
            # Vérifier fin de partie (plus de cartes dans les mains)
            if (hand_key in self.game_data and 
                (len(self.game_data['player1_hand']) == 0 or len(self.game_data['player2_hand']) == 0)):
                self.end_cards_game()
        else:
            # Un seul joueur a joué, c'est au tour de l'autre
            # Si c'est le début d'un nouveau tour après qu'un gagnant a été déterminé, nettoyer la table
            if self.game_data.get('round_winner') and not (player1_card and player2_card):
                logger.info("Cleaning table for new round")
                self.game_data['table_cards'] = {
                    'player1_card': card_data if player_key == 'player1' else None,
                    'player2_card': card_data if player_key == 'player2' else None
                }
                self.game_data['round_winner'] = None
            
            # Passer au tour de l'adversaire seulement si la table n'est pas pleine
            if not (self.game_data['table_cards']['player1_card'] and 
                    self.game_data['table_cards']['player2_card']):
                self.switch_turn()
        
        self.save()
        return True
    
    def determine_round_winner(self, card1, card2):
        """Déterminer le gagnant d'un tour de cartes."""
        # Convertir les cartes en valeurs numériques pour comparaison
        def card_value(card):
            rank = card['rank']
            if rank == 'A':
                return 14
            elif rank == 'K':
                return 13
            elif rank == 'Q':
                return 12
            elif rank == 'J':
                return 11
            else:
                return int(rank) if rank.isdigit() else 10
        
        value1 = card_value(card1)
        value2 = card_value(card2)
        
        logger.info(f"Card comparison: Player1 {card1['rank']}{card1['suit']} (value: {value1}) vs Player2 {card2['rank']}{card2['suit']} (value: {value2})")
        
        if value1 > value2:
            logger.info(f"Player1 wins with {card1['rank']}{card1['suit']} (value: {value1}) > {card2['rank']}{card2['suit']} (value: {value2})")
            return 'player1'
        elif value2 > value1:
            logger.info(f"Player2 wins with {card2['rank']}{card2['suit']} (value: {value2}) > {card1['rank']}{card1['suit']} (value: {value1})")
            return 'player2'
        else:
            # Égalité - le premier joueur gagne (ou autre règle)
            logger.info(f"Tie! Both cards have value {value1}. Player1 wins by default.")
            return 'player1'
    
    def end_cards_game(self):
        """Terminer la partie de cartes et déterminer le gagnant final."""
        player1_score = self.game_data['scores']['player1']
        player2_score = self.game_data['scores']['player2']
        
        if player1_score > player2_score:
            winner = self.player1
        elif player2_score > player1_score:
            winner = self.player2
        else:
            # Égalité - le joueur avec le plus de cartes restantes gagne
            player1_cards = len(self.game_data['player1_hand'])
            player2_cards = len(self.game_data['player2_hand'])
            winner = self.player1 if player1_cards > player2_cards else self.player2
        
        self.end_game(winner, reason='normal_end')

    def switch_turn(self):
        """Changer de joueur actuel."""
        # Pour Ludo, utiliser la méthode spécifique
        if hasattr(self.game_type, 'name') and self.game_type.name == 'ludo':
            self.switch_turn_ludo()
        else:
            # Pour les autres jeux, utiliser la méthode classique
            self.current_player = self.player2 if self.current_player == self.player1 else self.player1
        
        self.turn_start_time = timezone.now()
    
    def is_turn_timeout(self):
        """Vérifier si le timeout du tour est dépassé."""
        # Pour les dames et échecs compétitifs, le timer est géré par le moteur de jeu
        if self.game_type.name.lower() in ['dames', 'échecs', 'chess', 'ludo']:
            return False
        
        if not self.turn_start_time:
            return False
        
        elapsed = (timezone.now() - self.turn_start_time).seconds
        return elapsed > self.turn_timeout
    
    def handle_timeout(self):
        """Gérer le timeout d'un joueur."""
        # Le joueur actuel perd par timeout
        winner = self.player2 if self.current_player == self.player1 else self.player1
        self.end_game(winner, reason='timeout')
    
    def check_player_time_exhausted(self):
        """Vérifier si un joueur a épuisé son temps total."""
        if self.player1_time_left <= 0:
            return self.player2  # Player2 gagne
        elif self.player2_time_left <= 0:
            return self.player1  # Player1 gagne
        return None
    
    def update_player_time_on_move(self):
        """Mettre à jour le temps du joueur actuel quand il fait un mouvement."""
        if not self.turn_start_time:
            return
            
        time_used = (timezone.now() - self.turn_start_time).seconds
        
        if self.current_player == self.player1:
            self.player1_time_left = max(0, self.player1_time_left - time_used)
        elif self.current_player == self.player2:
            self.player2_time_left = max(0, self.player2_time_left - time_used)
        
        # Vérifier si le joueur a épuisé son temps
        winner_by_time = self.check_player_time_exhausted()
        if winner_by_time:
            self.end_game(winner_by_time, reason='time_exhausted')
            return True
        
        return False
    
    def check_win_condition(self):
        """Vérifier les conditions de victoire selon le type de jeu."""
        win_checker_map = {
            'chess': self.check_chess_win,
            'Chess': self.check_chess_win,
            'Échecs': self.check_chess_win,
            'échecs': self.check_chess_win,
            'checkers': self.check_checkers_win,
            'Checkers': self.check_checkers_win,
            'Dames': self.check_checkers_win,
            'dames': self.check_checkers_win,
            'ludo': self.check_ludo_win,
            'Ludo': self.check_ludo_win,
            'cards': self.check_cards_win,
            'Cards': self.check_cards_win,
            'cartes': self.check_cards_win,
            'Cartes': self.check_cards_win,
        }
        
        checker = win_checker_map.get(self.game_type.name)
        return checker() if checker else False
    
    def check_checkers_win(self):
        """Vérifier les conditions de victoire aux dames."""
        # Vérifier s'il reste des pièces à l'adversaire
        return False
    
    def check_ludo_win(self):
        """Vérifier les conditions de victoire au ludo."""
        pieces = self.game_data.get('pieces', {})
        active_colors = self.game_data.get('active_colors', ['red', 'blue'])
        
        for color in active_colors:
            if color not in pieces:
                continue
                
            color_pieces = pieces[color]
            # Vérifier si toutes les pièces de cette couleur sont arrivées (position 58 = centre final)
            all_finished = all(piece['position'] == 58 for piece in color_pieces)
            if all_finished:
                # Trouver le joueur avec cette couleur
                player_colors = self.game_data.get('player_colors', {})
                for user_id, player_color in player_colors.items():
                    if player_color == color:
                        if user_id == str(self.player1.id):
                            return self.player1
                        elif self.player2 and user_id == str(self.player2.id):
                            return self.player2
        
        return None
    
    def check_cards_win(self):
        """Vérifier les conditions de victoire aux cartes."""
        # Vérifier si un joueur n'a plus de cartes
        return False
    
    def end_game(self, winner, reason='victory'):
        """Terminer la partie et distribuer automatiquement le winner_prize."""
        self.winner = winner
        self.status = 'finished'
        self.finished_at = timezone.now()
        
        # ✅ Synchroniser le statut dans game_data
        if self.game_data:
            self.game_data['status'] = 'finished'
        
        # ✅ VÉRIFIER D'ABORD si les scores sont égaux (priorité haute)
        is_equal_score = False
        if self.game_type.name.lower() in ['dames', 'checkers'] and self.game_data:
            red_score = self.game_data.get('red_score', {}).get('points', 0)
            black_score = self.game_data.get('black_score', {}).get('points', 0)
            is_equal_score = (red_score == black_score)
            logger.info(f"🎯 Score check (Checkers): RED={red_score}, BLACK={black_score}, Equal={is_equal_score}")
        elif self.game_type.name.lower() in ['echecs', 'chess'] and self.game_data:
            white_score = self.game_data.get('white_score', {}).get('points', 0)
            black_score = self.game_data.get('black_score', {}).get('points', 0)
            is_equal_score = (white_score == black_score)
            logger.info(f"🎯 Score check (Chess): WHITE={white_score}, BLACK={black_score}, Equal={is_equal_score}")
        elif self.game_type.name.lower() == 'ludo' and self.game_data:
            # Pour Ludo, comparer les scores des couleurs actives
            active_colors = self.game_data.get('active_colors', [])
            if len(active_colors) == 2:
                score1 = self.game_data.get(f'{active_colors[0]}_score', {}).get('points', 0)
                score2 = self.game_data.get(f'{active_colors[1]}_score', {}).get('points', 0)
                is_equal_score = (score1 == score2)
                logger.info(f"🎯 Score check (Ludo): {active_colors[0]}={score1}, {active_colors[1]}={score2}, Equal={is_equal_score}")
        
        # ✅ Distribuer les gains selon le résultat
        if self.winner_prize > 0:
            # CAS 1: Scores égaux - TOUJOURS partager 50/50
            if is_equal_score:
                half_prize = self.winner_prize / 2
                logger.info(f"💰 EQUAL SCORES! Sharing {half_prize} {self.currency} with each player")
                
                if self.player1:
                    self.player1.update_balance(self.currency, half_prize, 'add')
                    logger.info(f"💰 {self.player1.username} received {half_prize} {self.currency}")
                
                if self.player2:
                    self.player2.update_balance(self.currency, half_prize, 'add')
                    logger.info(f"💰 {self.player2.username} received {half_prize} {self.currency}")
                
                # Marquer comme match nul dans game_data
                if self.game_data:
                    self.game_data['game_result'] = self.game_data.get('game_result', {})
                    self.game_data['game_result']['winner'] = 'draw'
                    self.game_data['game_result']['reason'] = 'equal_scores'
                    self.game_data['game_result']['prize_distribution'] = {
                        'player1': float(half_prize),
                        'player2': float(half_prize)
                    }
            
            # CAS 2: Match nul déclaré
            elif reason == 'draw' or winner == 'draw' or not winner:
                half_prize = self.winner_prize / 2
                logger.info(f"💰 DRAW! Distributing {half_prize} {self.currency} to each player")
                
                if self.player1:
                    self.player1.update_balance(self.currency, half_prize, 'add')
                    logger.info(f"💰 {self.player1.username} received {half_prize} {self.currency}")
                
                if self.player2:
                    self.player2.update_balance(self.currency, half_prize, 'add')
                    logger.info(f"💰 {self.player2.username} received {half_prize} {self.currency}")
                
                # Marquer comme match nul dans game_data
                if self.game_data:
                    self.game_data['game_result'] = self.game_data.get('game_result', {})
                    self.game_data['game_result']['winner'] = 'draw'
                    self.game_data['game_result']['prize_distribution'] = {
                        'player1': float(half_prize),
                        'player2': float(half_prize)
                    }
            
            # CAS 3: Victoire nette
            elif winner and winner != 'draw':
                logger.info(f"💰 WINNER! Distributing {self.winner_prize} {self.currency} to {winner.username}")
                winner.update_balance(self.currency, self.winner_prize, 'add')
                
                if self.game_data:
                    self.game_data['game_result'] = self.game_data.get('game_result', {})
                    self.game_data['game_result']['prize_distribution'] = {
                        'winner': winner.username,
                        'amount': float(self.winner_prize)
                    }
        
        # Enregistrer les statistiques
        self.update_player_statistics(reason)
        
        self.save()
    
    def update_player_statistics(self, reason):
        from apps.analytics.models import PlayerStats

        # Mise à jour stats pour player1
        stats1, created = PlayerStats.objects.get_or_create(player_id=str(self.player1.id))
        stats1.total_sessions += 1
        stats1.highest_score = max(stats1.highest_score, int(self.winner_prize))
        stats1.highest_level = max(stats1.highest_level, 1)  # adapter si vous avez un niveau réel
        stats1.total_playtime += int((self.finished_at - self.started_at).total_seconds()) if self.finished_at and self.started_at else 0
        if created:
            stats1.first_played = self.created_at
        stats1.last_played = timezone.now()
        stats1.save()

        # Mise à jour stats pour player2 (si présent)
        if self.player2:
            stats2, created = PlayerStats.objects.get_or_create(player_id=str(self.player2.id))
            stats2.total_sessions += 1
            stats2.highest_score = max(stats2.highest_score, int(self.winner_prize))
            stats2.highest_level = max(stats2.highest_level, 1)
            stats2.total_playtime += int((self.finished_at - self.started_at).total_seconds()) if self.finished_at and self.started_at else 0
            if created:
                stats2.first_played = self.created_at
            stats2.last_played = timezone.now()
            stats2.save()

    
    def cancel_game(self, reason='cancelled'):
        """Annuler la partie et rembourser les mises."""
        if self.status in ['finished', 'cancelled']:
            return
        
        self.status = 'cancelled'
        self.finished_at = timezone.now()
        
        # Rembourser les mises
        if self.player1:
            self.player1.update_balance(self.currency, self.bet_amount, 'add')
        if self.player2:
            self.player2.update_balance(self.currency, self.bet_amount, 'add')
        
        self.save()
    
    def get_opponent(self, player):
        """Obtenir l'adversaire d'un joueur."""
        if player == self.player1:
            return self.player2
        elif player == self.player2:
            return self.player1
        return None
    
    def get_time_left(self, player):
        """Obtenir le temps restant pour un joueur."""
        if player == self.player1:
            return self.player1_time_left
        elif player == self.player2:
            return self.player2_time_left
        return 0
    
    def update_time_left(self, player, time_used):
        """Mettre à jour le temps restant d'un joueur."""
        if player == self.player1:
            self.player1_time_left = max(0, self.player1_time_left - time_used)
        elif player == self.player2:
            self.player2_time_left = max(0, self.player2_time_left - time_used)
        
        self.save(update_fields=['player1_time_left', 'player2_time_left'])

    # ===== CHESS GAME METHODS =====
    
    def process_chess_move(self, player, move_data):
        """Traiter un mouvement d'échecs COMPÉTITIF avec timer et scoring."""
        logger.info(f"🎯 PROCESS_CHESS_MOVE START for player {player.username}")
        logger.info(f"🎯 Game ID: {self.id}, Room: {self.room_code}")
        logger.info(f"🎯 Move data: {move_data}")
        
        try:
            from apps.games.game_logic.chess import ChessGameEngine
            from apps.games.game_logic.chess_competitive import (
                ChessTimer,
                ChessScore,
                check_competitive_chess_game_over,
                check_and_auto_pass_turn_if_timeout,
                update_score_for_capture,
                convert_chess_board_to_unicode
            )
            
            # NOUVEAU: Vérifier si le joueur précédent a dépassé 20s et passer auto son tour
            new_game_data, turn_was_passed = check_and_auto_pass_turn_if_timeout(self.game_data)
            if turn_was_passed:
                logger.warning(f"⏰ Turn auto-passed due to 20s timeout")
                self.game_data = new_game_data
                # Mettre à jour current_player du jeu
                current_color = self.game_data.get('current_player', 'white')
                if current_color == 'white':
                    self.current_player = self.player1
                else:
                    self.current_player = self.player2
                self.save()
            
            # Vérifier que c'est le tour du joueur
            if not self.is_player_turn_chess(player):
                logger.error(f"Not {player.username}'s turn in chess")
                return False
            
            # Initialiser le moteur avec l'état actuel
            engine = ChessGameEngine()
            
            # Charger le plateau depuis game_data
            if self.game_data and 'board' in self.game_data:
                board_data = self.game_data['board']
            else:
                logger.error("No board data found in game_data")
                return False
            
            # Effectuer le mouvement
            from_pos = move_data.get('from')
            to_pos = move_data.get('to')
            promotion = move_data.get('promotion')
            
            # Vérifier si c'est une capture
            from_row, from_col = self.notation_to_indices(from_pos)
            to_row, to_col = self.notation_to_indices(to_pos)
            
            captured_piece = None
            if board_data[to_row][to_col] is not None:
                captured_piece = board_data[to_row][to_col]
                logger.info(f"📊 Capture detected: {captured_piece}")
            
            # Valider et effectuer le mouvement (logique simplifiée)
            moving_piece = board_data[from_row][from_col]
            if moving_piece is None:
                logger.error(f"No piece at {from_pos}")
                return False
            
            # Vérifier que la pièce appartient au joueur actuel
            current_color = self.game_data.get('current_player', 'white')
            if moving_piece.get('color') != current_color:
                logger.error(f"Piece at {from_pos} is not {current_color}")
                return False
            
            # ✅ Vérifier que le mouvement est légal (ne laisse pas le roi en échec)
            from apps.games.game_logic.chess_competitive import (
                is_move_legal,
                get_possible_moves
            )
            
            # Vérifier si le mouvement est dans les coups possibles
            possible_moves = get_possible_moves(board_data, from_row, from_col)
            if (to_row, to_col) not in possible_moves:
                logger.error(f"Move {from_pos}->{to_pos} is not a valid move for this piece")
                return False
            
            # Vérifier que le mouvement ne laisse pas le roi en échec
            if not is_move_legal(board_data, from_row, from_col, to_row, to_col, current_color):
                logger.error(f"Move {from_pos}->{to_pos} would leave king in check")
                return False
            
            # Effectuer le mouvement sur le plateau
            board_data[to_row][to_col] = moving_piece
            board_data[from_row][from_col] = None
            
            # Marquer la pièce comme déplacée
            moving_piece['has_moved'] = True
            
            # ✅ Mettre à jour halfmove_clock (règle des 50 coups)
            # Réinitialiser si capture ou mouvement de pion
            if captured_piece or moving_piece.get('type') == 'P':
                self.game_data['halfmove_clock'] = 0
            else:
                self.game_data['halfmove_clock'] = self.game_data.get('halfmove_clock', 0) + 1
            
            # Gérer la promotion
            if promotion and moving_piece.get('type') == 'P':
                if (current_color == 'white' and to_row == 0) or (current_color == 'black' and to_row == 7):
                    moving_piece['type'] = promotion.upper()
                    logger.info(f"♛ Pawn promoted to {promotion}")
            
            # Mettre à jour les scores en cas de capture
            if captured_piece:
                captured_type = captured_piece.get('type')
                if current_color == 'white':
                    score = ChessScore.from_dict(self.game_data.get('white_score', {}))
                    update_score_for_capture(score, captured_type)
                    self.game_data['white_score'] = score.to_dict()
                else:
                    score = ChessScore.from_dict(self.game_data.get('black_score', {}))
                    update_score_for_capture(score, captured_type)
                    self.game_data['black_score'] = score.to_dict()
            
            # Ajouter le mouvement à l'historique
            if not hasattr(self, 'move_history') or self.move_history is None:
                self.move_history = []
            
            self.move_history.append({
                'player': player.username,
                'move': {
                    'from': from_pos,
                    'to': to_pos,
                    'promotion': promotion,
                    'captured': captured_piece.get('type') if captured_piece else None,
                    'action': 'MOVE_PIECE'
                },
                'timestamp': timezone.now().isoformat(),
                'turn_number': len(self.move_history) + 1,
                'notation': f"{from_pos}{to_pos}"
            })
            
            # Mettre à jour last_move_at
            self.last_move_at = timezone.now()
            
            # Mettre à jour le board Unicode
            self.game_data['board_unicode'] = convert_chess_board_to_unicode(self.game_data)
            
            # ✅ Enregistrer la position dans l'historique pour détecter la triple répétition
            from apps.games.game_logic.chess_competitive import board_to_position_hash
            position_hash = board_to_position_hash(
                self.game_data['board'],
                self.game_data.get('current_player', 'white'),
                self.game_data.get('castling_rights', {}),
                self.game_data.get('en_passant_target')
            )
            if 'position_history' not in self.game_data:
                self.game_data['position_history'] = []
            self.game_data['position_history'].append(position_hash)
            
            # Mettre à jour le timer
            timer = ChessTimer.from_dict(self.game_data.get('timer', {}))
            timer.switch_player()
            self.game_data['timer'] = timer.to_dict()
            
            # Changer le joueur actuel
            self.switch_chess_turn()
            
            # Vérifier fin de partie
            is_over, winner, details = check_competitive_chess_game_over(self.game_data)
            if is_over:
                self.game_data['is_game_over'] = True
                self.game_data['winner'] = winner
                self.game_data['game_over_details'] = details
                
                # Terminer le jeu et distribuer les prix
                if winner == 'white':
                    self.end_game(self.player1, reason='victory')
                elif winner == 'black':
                    self.end_game(self.player2, reason='victory')
                else:
                    self.end_game(None, reason='draw')
            
            self.save()
            logger.info(f"✅ Chess move processed successfully: {from_pos} -> {to_pos}")
            return True
            
        except Exception as e:
            logger.error(f"❌ Error processing chess move: {e}", exc_info=True)
            return False
    
    def is_player_turn_chess(self, player):
        """Vérifier si c'est le tour du joueur aux échecs."""
        current_color = self.game_data.get('current_player', 'white')
        
        # player1 = blanc, player2 = noir
        if player == self.player1 and current_color == 'white':
            return True
        if player == self.player2 and current_color == 'black':
            return True
        
        return False
    
    def notation_to_indices(self, notation: str) -> tuple:
        """Convertir notation algébrique (e2, e4) en indices (row, col)."""
        col = ord(notation[0].lower()) - ord('a')
        row = 8 - int(notation[1])
        return row, col
    
    def switch_chess_turn(self):
        """Changer le tour aux échecs."""
        # Utiliser le current_player du timer comme source de vérité
        timer_data = self.game_data.get('timer', {})
        next_color = timer_data.get('current_player', 'white')
        self.game_data['current_player'] = next_color
        
        # Mettre à jour current_player du jeu
        if next_color == 'white':
            self.current_player = self.player1
        else:
            self.current_player = self.player2
    
    def update_simple_chess_board(self, engine):
        """Mettre à jour le board simplifié pour le frontend."""
        try:
            # Mapping des pièces du moteur vers les caractères Unicode
            piece_mapping = {
                # Pieces blanches
                'K': '♔', 'Q': '♕', 'R': '♖', 'B': '♗', 'N': '♘', 'P': '♙',
                # Pieces noires  
                'k': '♚', 'q': '♛', 'r': '♜', 'b': '♝', 'n': '♞', 'p': '♟'
            }
            
            # Obtenir le board du moteur
            chess_state = engine.get_game_state()
            engine_board = chess_state.get('board', [])
            
            if not engine_board:
                return
                
            simple_board = []
            for row in engine_board:
                simple_row = []
                for cell in row:
                    if cell is None:
                        # Case vide
                        simple_row.append('.')
                    elif isinstance(cell, dict) and 'type' in cell and 'color' in cell:
                        # Format objet du moteur: {'type': 'R', 'color': 'black', 'has_moved': False}
                        piece_type = cell['type']
                        color = cell['color']
                        
                        if piece_type and color:
                            # Convertir en format standard (majuscule = blanc, minuscule = noir)
                            if color.lower() == 'white':
                                piece_char = piece_type.upper()
                            else:
                                piece_char = piece_type.lower()
                            
                            unicode_piece = piece_mapping.get(piece_char, '.')
                            simple_row.append(unicode_piece)
                        else:
                            simple_row.append('.')
                    elif isinstance(cell, str):
                        # Format string simple (fallback)
                        simple_row.append(piece_mapping.get(cell, '.'))
                    else:
                        simple_row.append('.')
                simple_board.append(simple_row)
            
            self.game_data['board'] = simple_board
            logger.info(f"Chess board updated successfully, sample: {simple_board[0][:4]} / {simple_board[7][:4]}")
            
        except Exception as e:
            logger.error(f"Error updating simple chess board: {e}")
            # Fallback au board par défaut
            self.game_data['board'] = [
                ['♜', '♞', '♝', '♛', '♚', '♝', '♞', '♜'],
                ['♟', '♟', '♟', '♟', '♟', '♟', '♟', '♟'],
                ['.', '.', '.', '.', '.', '.', '.', '.'],
                ['.', '.', '.', '.', '.', '.', '.', '.'],
                ['.', '.', '.', '.', '.', '.', '.', '.'],
                ['.', '.', '.', '.', '.', '.', '.', '.'],
                ['♙', '♙', '♙', '♙', '♙', '♙', '♙', '♙'],
                ['♖', '♘', '♗', '♕', '♔', '♗', '♘', '♖']
            ]
    
    def check_chess_win(self):
        """Vérifier les conditions de victoire aux échecs COMPÉTITIFS."""
        try:
            from apps.games.game_logic.chess_competitive import check_competitive_chess_game_over
            
            if not self.game_data:
                return None
            
            # Vérifier fin de partie (timeout, échec et mat, etc.)
            is_over, winner, details = check_competitive_chess_game_over(self.game_data)
            
            if is_over:
                # ✅ RESPECTER le winner renvoyé par check_competitive_chess_game_over
                # Il gère déjà:
                # - Échec et mat → winner = 'white' ou 'black'
                # - Stalemate (pat) → winner = 'draw'
                # - Matériel insuffisant → winner = 'draw'
                # - Règle des 50 coups → winner = 'draw'
                # - Timeout global avec comparaison de points → winner basé sur les points
                
                if winner == 'draw':
                    # Match nul officiel (pat, matériel insuffisant, etc.)
                    return None
                elif winner == 'white':
                    return self.player1
                elif winner == 'black':
                    return self.player2
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking chess win: {e}")
            return None

    # =============================================================================
    # MÉTHODES POUR LES DAMES 10x10 INTERNATIONALES
    # =============================================================================
    
    def process_checkers_move(self, player, move_data):
        """Traiter un mouvement de dames 10x10 compétitif."""
        try:
            logger.info(f"🎯 PROCESS_CHECKERS_MOVE START for player {player.username}")
            logger.info(f"🎯 Game ID: {self.id}, Room: {self.room_code}")
            logger.info(f"🎯 Move data: {move_data}")
            
            from apps.games.game_logic.checkers_competitive import (
                make_competitive_move,
                check_competitive_game_over,
                create_competitive_checkers_game,
                convert_board_to_unicode,
                check_and_auto_pass_turn_if_timeout
            )
            
            # NOUVEAU: Vérifier si le joueur précédent a dépassé 20s
            # Si oui, passer automatiquement son tour
            new_game_data, turn_was_passed = check_and_auto_pass_turn_if_timeout(self.game_data)
            if turn_was_passed:
                logger.warning(f"⏰ Turn auto-passed due to 20s timeout")
                self.game_data = new_game_data
                self.save()
            
            # Vérifier que c'est le tour du joueur
            if not self.is_player_turn_checkers(player):
                logger.error(f"Not {player.username}'s turn in checkers")
                return False
            
            logger.info(f"🎯 Player turn validated for {player.username}")
            
            # Utiliser l'état du jeu existant (déjà initialisé par initialize_checkers)
            # ✅ CRITIQUE: Vérifier que game_data n'est pas None/vide
            if not self.game_data or not isinstance(self.game_data, dict) or 'board' not in self.game_data:
                logger.error(f"❌ game_data is empty or invalid! Reloading from DB...")
                self.refresh_from_db()
                if not self.game_data or not isinstance(self.game_data, dict) or 'board' not in self.game_data:
                    logger.error(f"❌ game_data still empty after refresh! Cannot process move.")
                    return False
            
            game_state = self.game_data
            
            # Extraire les positions
            from_pos = move_data.get('from')  # Format: [row, col] ou "row,col"
            to_pos = move_data.get('to')  # Format: [row, col] ou "row,col"
            
            if isinstance(from_pos, str):
                from_row, from_col = map(int, from_pos.split(','))
            else:
                from_row, from_col = from_pos
            
            if isinstance(to_pos, str):
                to_row, to_col = map(int, to_pos.split(','))
            else:
                to_row, to_col = to_pos
            
            logger.info(f"🎯 Executing move: ({from_row},{from_col}) -> ({to_row},{to_col})")
            
            # Effectuer le mouvement avec le moteur compétitif
            result = make_competitive_move(
                game_state, 
                from_row, 
                from_col, 
                to_row, 
                to_col
            )
            
            if not result['success']:
                logger.error(f"Checkers move failed: {result.get('error')}")
                return False
            
            logger.info(f"🎯 Move executed successfully! Points gained: {result['points_gained']}")
            
            # Mettre à jour l'état du jeu
            self.game_data = result['game_state']
            
            # Ajouter le board en format Unicode pour le frontend
            self.game_data['board_unicode'] = convert_board_to_unicode(self.game_data)
            
            # ✅ AJOUT: Ajouter le mouvement à l'historique
            if not hasattr(self, 'move_history') or self.move_history is None:
                self.move_history = []
            
            self.move_history.append({
                'player': player.username,
                'move': {
                    'from': [from_row, from_col],
                    'to': [to_row, to_col],
                    'action': 'MOVE_PIECE'
                },
                'timestamp': timezone.now().isoformat(),
                'turn_number': len(self.move_history) + 1,
                'points_gained': result.get('points_gained', 0),
                'captured': result.get('captured', False)
            })
            
            logger.info(f"🎯 Move added to history, total moves: {len(self.move_history)}")
            
            # Vérifier si la partie est terminée
            if result.get('is_game_over'):
                winner_color = result.get('winner')
                logger.info(f"🎯 Game over! Winner: {winner_color}")
                
                # Déterminer le gagnant
                winner = None
                reason = 'victory'
                
                if winner_color == 'red':
                    winner = self.player1
                    reason = 'victory'
                elif winner_color == 'black':
                    winner = self.player2
                    reason = 'victory'
                elif winner_color == 'draw' or winner_color is None:
                    # Match nul - scores égaux ou timeout
                    winner = None
                    reason = 'draw'
                    logger.info(f"🎯 Game ended in DRAW")
                
                # ✅ TOUJOURS appeler end_game pour distribuer les prix
                self.end_game(winner, reason=reason)
            
            # ✅ Mettre à jour les timestamps
            self.last_move_at = timezone.now()
            
            # ✅ CRITIQUE: Synchroniser le current_player de la DB avec celui du game_data
            # UNIQUEMENT POUR LES DAMES (checkers) - pas pour Ludo qui utilise des couleurs directement
            current_player_color = self.game_data.get('current_player')
            if current_player_color == 'red':
                self.current_player = self.player1
                logger.info(f"🔄 Updated current_player to RED (player1: {self.player1.username})")
            elif current_player_color == 'black':
                self.current_player = self.player2
                logger.info(f"🔄 Updated current_player to BLACK (player2: {self.player2.username})")
            
            # ℹ️ Le timer est déjà mis à jour par le moteur de jeu dans result['game_state']
            # Pas besoin de le modifier manuellement ici
            if 'timer' in self.game_data:
                logger.info(f"🎯 Timer from engine: current_move_start={self.game_data['timer'].get('current_move_start')}")
            
            # Sauvegarder dans la base de données
            logger.info(f"🎯 Saving to database...")
            # ✅ FORCER la mise à jour des JSONFields en spécifiant update_fields
            self.save(update_fields=['game_data', 'move_history', 'last_move_at', 'current_player', 'status', 'finished_at'])
            logger.info(f"🎯 SAVED TO DATABASE!")
            
            logger.info(f"🎯 PROCESS_CHECKERS_MOVE COMPLETED")
            return True
            
        except Exception as e:
            logger.error(f"🎯 ERROR processing checkers move: {e}")
            return False
    
    def is_player_turn_checkers(self, player):
        """Vérifier si c'est le tour du joueur aux dames compétitives."""
        current_color = self.game_data.get('current_player', 'red')
        
        # ✅ MOTEUR COMPÉTITIF: player1 = RED, player2 = BLACK
        if player == self.player1 and current_color == 'red':
            return True
        if player == self.player2 and current_color == 'black':
            return True
        
        logger.debug(f"Turn check failed: player={player.username}, current_color={current_color}, player1={self.player1.username}, player2={self.player2.username if self.player2 else 'None'}")
        return False
    
    def switch_checkers_turn(self):
        """Changer le tour aux dames."""
        current_color = self.game_data.get('current_player', 'light')
        next_color = 'dark' if current_color == 'light' else 'light'
        self.game_data['current_player'] = next_color
        
        # Mettre à jour current_player du jeu
        if next_color == 'light':
            self.current_player = self.player1
        else:
            self.current_player = self.player2
            
        # Démarrer le chronomètre pour le nouveau joueur
        self.turn_start_time = timezone.now()
    
    def update_simple_checkers_board(self, engine):
        """Mettre à jour le board simplifié pour le frontend (dames 10x10)."""
        try:
            # Mapping des pièces du moteur vers les caractères Unicode
            piece_mapping = {
                # Pions noirs (sombres)
                'black_man': '⚫',
                'black_king': '♛',
                # Pions blancs (clairs) 
                'red_man': '⚪',
                'red_king': '♕',
                # Aussi support pour d'autres formats possibles
                'dark_pawn': '⚫',
                'dark_king': '♛',
                'light_pawn': '⚪',
                'light_king': '♕',
                # Case vide
                None: '.',
                '': '.'
            }
            
            game_state = engine.get_game_state()
            engine_board = game_state['board']
            simple_board = []
            
            # Convertir le board 10x10
            for row_data in engine_board:
                simple_row = []
                for cell in row_data:
                    if isinstance(cell, dict):
                        # Format objet avec type et couleur
                        piece_type = cell.get('type', '')
                        piece_color = cell.get('color', '')
                        
                        if piece_color and piece_type:
                            key = f"{piece_color}_{piece_type}"
                            simple_row.append(piece_mapping.get(key, '.'))
                        else:
                            simple_row.append('.')
                    elif isinstance(cell, str):
                        # Format string simple
                        simple_row.append(piece_mapping.get(cell, '.'))
                    else:
                        simple_row.append('.')
                simple_board.append(simple_row)
            
            self.game_data['board'] = simple_board
            logger.info(f"Checkers board updated successfully, sample: {simple_board[0][:4]} / {simple_board[9][:4]}")
            
        except Exception as e:
            logger.error(f"Error updating simple checkers board: {e}")
            # Fallback au board par défaut 10x10
            self.game_data['board'] = [
                ['.', '⚫', '.', '⚫', '.', '⚫', '.', '⚫', '.', '⚫'],
                ['⚫', '.', '⚫', '.', '⚫', '.', '⚫', '.', '⚫', '.'],
                ['.', '⚫', '.', '⚫', '.', '⚫', '.', '⚫', '.', '⚫'],
                ['⚫', '.', '⚫', '.', '⚫', '.', '⚫', '.', '⚫', '.'],
                ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.'],
                ['.', '.', '.', '.', '.', '.', '.', '.', '.', '.'],
                ['.', '⚪', '.', '⚪', '.', '⚪', '.', '⚪', '.', '⚪'],
                ['⚪', '.', '⚪', '.', '⚪', '.', '⚪', '.', '⚪', '.'],
                ['.', '⚪', '.', '⚪', '.', '⚪', '.', '⚪', '.', '⚪'],
                ['⚪', '.', '⚪', '.', '⚪', '.', '⚪', '.', '⚪', '.']
            ]
    
    def check_checkers_win(self):
        """Vérifier les conditions de victoire aux dames."""
        try:
            from apps.games.game_logic.checkers import CheckersGameEngine
            
            if not self.game_data or 'checkers_state' not in self.game_data:
                return None
            
            engine = CheckersGameEngine()
            # CORRECTION: from_dict retourne un nouveau board, il faut l'assigner
            engine.board = engine.board.from_dict(self.game_data['checkers_state'])
            game_state = engine.get_game_state()
            
            # Vérifier si la partie est terminée
            game_result = game_state.get('game_result')
            
            if game_result:
                if game_result.get('winner') == 'light':
                    return self.player1
                elif game_result.get('winner') == 'dark':
                    return self.player2
                # Sinon c'est un match nul
            
            return None
            
        except Exception as e:
            logger.error(f"Error checking checkers win: {e}")
            return None


class GameInvitation(models.Model):
    """Invitations à des parties privées."""
    
    STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('accepted', _('Acceptée')),
        ('declined', _('Refusée')),
        ('expired', _('Expirée')),
        ('cancelled', _('Annulée')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name='invitations',
        verbose_name=_('Partie')
    )
    inviter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='sent_invitations',
        verbose_name=_('Invitant')
    )
    invitee = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_invitations',
        verbose_name=_('Invité')
    )
    
    status = models.CharField(_('Statut'), max_length=20, choices=STATUS_CHOICES, default='pending')
    message = models.TextField(_('Message'), blank=True)
    
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    responded_at = models.DateTimeField(_('Répondu le'), null=True, blank=True)
    expires_at = models.DateTimeField(_('Expire le'))
    
    class Meta:
        db_table = 'game_invitations'
        verbose_name = _('Invitation de partie')
        verbose_name_plural = _('Invitations de parties')
        unique_together = ['game', 'invitee']
    
    def __str__(self):
        return f"{self.inviter.username} → {self.invitee.username} ({self.game.room_code})"
    
    def accept(self):
        """Accepter l'invitation."""
        if self.status != 'pending':
            raise ValidationError(_('Cette invitation n\'est plus valide'))
        
        if timezone.now() > self.expires_at:
            self.status = 'expired'
            self.save()
            raise ValidationError(_('Cette invitation a expiré'))
        
        # Rejoindre la partie
        self.game.join_game(self.invitee)
        
        self.status = 'accepted'
        self.responded_at = timezone.now()
        self.save()
    
    def decline(self):
        """Refuser l'invitation."""
        if self.status != 'pending':
            raise ValidationError(_('Cette invitation n\'est plus valide'))
        
        self.status = 'declined'
        self.responded_at = timezone.now()
        self.save()


class GameReport(models.Model):
    """Signalements de parties."""
    
    REPORT_TYPES = [
        ('cheating', _('Triche')),
        ('inappropriate_behavior', _('Comportement inapproprié')),
        ('harassment', _('Harcèlement')),
        ('technical_issue', _('Problème technique')),
        ('other', _('Autre')),
    ]
    
    STATUS_CHOICES = [
        ('pending', _('En attente')),
        ('under_review', _('En cours de traitement')),
        ('resolved', _('Résolu')),
        ('dismissed', _('Rejeté')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    game = models.ForeignKey(
        Game,
        on_delete=models.CASCADE,
        related_name='reports',
        verbose_name=_('Partie')
    )
    reporter = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='submitted_reports',
        verbose_name=_('Signalant')
    )
    reported_user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='received_reports',
        verbose_name=_('Utilisateur signalé')
    )
    
    report_type = models.CharField(_('Type de signalement'), max_length=30, choices=REPORT_TYPES)
    description = models.TextField(_('Description'))
    evidence = models.JSONField(_('Preuves'), default=dict, blank=True)
    
    status = models.CharField(_('Statut'), max_length=20, choices=STATUS_CHOICES, default='pending')
    admin_notes = models.TextField(_('Notes admin'), blank=True)
    resolved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_reports',
        verbose_name=_('Résolu par')
    )
    
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    resolved_at = models.DateTimeField(_('Résolu le'), null=True, blank=True)
    
    class Meta:
        db_table = 'game_reports'
        verbose_name = _('Signalement de partie')
        verbose_name_plural = _('Signalements de parties')
        ordering = ['-created_at']
    
    def __str__(self):
        return f"Signalement #{self.id.hex[:8]} - {self.get_report_type_display()}"


class Tournament(models.Model):
    """Tournois organisés."""
    
    TOURNAMENT_TYPES = [
        ('single_elimination', _('Élimination directe')),
        ('double_elimination', _('Double élimination')),
        ('round_robin', _('Round robin')),
        ('swiss', _('Système suisse')),
    ]
    
    STATUS_CHOICES = [
        ('upcoming', _('À venir')),
        ('registration', _('Inscriptions ouvertes')),
        ('ready', _('Prêt à commencer')),
        ('ongoing', _('En cours')),
        ('finished', _('Terminé')),
        ('cancelled', _('Annulé')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(_('Nom'), max_length=200)
    description = models.TextField(_('Description'))
    
    game_type = models.ForeignKey(
        GameType,
        on_delete=models.CASCADE,
        related_name='tournaments',
        verbose_name=_('Type de jeu')
    )
    
    tournament_type = models.CharField(_('Type de tournoi'), max_length=20, choices=TOURNAMENT_TYPES)
    
    # Configuration
    max_participants = models.PositiveIntegerField(_('Participants maximum'))
    entry_fee = models.DecimalField(_('Frais d\'inscription'), max_digits=10, decimal_places=2)
    currency = models.CharField(_('Devise'), max_length=5, choices=Game.CURRENCIES, default='FCFA')
    
    # Prix
    total_prize_pool = models.DecimalField(_('Cagnotte totale'), max_digits=12, decimal_places=2, default=0)
    winner_prize = models.DecimalField(_('Prix du gagnant'), max_digits=10, decimal_places=2, default=0)
    runner_up_prize = models.DecimalField(_('Prix du finaliste'), max_digits=10, decimal_places=2, default=0)
    
    # Timing
    registration_start = models.DateTimeField(_('Début des inscriptions'))
    registration_end = models.DateTimeField(_('Fin des inscriptions'))
    start_date = models.DateTimeField(_('Date de début'))
    end_date = models.DateTimeField(_('Date de fin'), null=True, blank=True)
    
    status = models.CharField(_('Statut'), max_length=20, choices=STATUS_CHOICES, default='upcoming')
    
    # Organisateur
    organizer = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='organized_tournaments',
        verbose_name=_('Organisateur')
    )
    
    # Métadonnées
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        db_table = 'tournaments'
        verbose_name = _('Tournoi')
        verbose_name_plural = _('Tournois')
        ordering = ['start_date']
    
    def __str__(self):
        return self.name


class TournamentParticipant(models.Model):
    """Participants aux tournois."""
    
    tournament = models.ForeignKey(
        Tournament,
        on_delete=models.CASCADE,
        related_name='participants',
        verbose_name=_('Tournoi')
    )
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tournament_participations',
        verbose_name=_('Utilisateur')
    )
    
    seed = models.PositiveIntegerField(_('Tête de série'), null=True, blank=True)
    current_round = models.PositiveIntegerField(_('Tour actuel'), default=1)
    is_eliminated = models.BooleanField(_('Éliminé'), default=False)
    final_position = models.PositiveIntegerField(_('Position finale'), null=True, blank=True)
    
    registered_at = models.DateTimeField(_('Inscrit le'), auto_now_add=True)
    
    class Meta:
        db_table = 'tournament_participants'
        verbose_name = _('Participant au tournoi')
        verbose_name_plural = _('Participants aux tournois')
        unique_together = ['tournament', 'user']
    
    def __str__(self):
        return f"{self.user.username} - {self.tournament.name}"


class Leaderboard(models.Model):
    """Classements des joueurs."""
    
    LEADERBOARD_TYPES = [
        ('global', _('Global')),
        ('monthly', _('Mensuel')),
        ('weekly', _('Hebdomadaire')),
        ('game_type', _('Par type de jeu')),
    ]
    
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='leaderboard_entries',
        verbose_name=_('Utilisateur')
    )
    
    leaderboard_type = models.CharField(_('Type de classement'), max_length=20, choices=LEADERBOARD_TYPES)
    game_type = models.ForeignKey(
        GameType,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='leaderboard_entries',
        verbose_name=_('Type de jeu')
    )
    
    # Statistiques
    rank = models.PositiveIntegerField(_('Rang'))
    points = models.PositiveIntegerField(_('Points'), default=0)
    games_played = models.PositiveIntegerField(_('Parties jouées'), default=0)
    games_won = models.PositiveIntegerField(_('Parties gagnées'), default=0)
    win_rate = models.DecimalField(_('Taux de victoire'), max_digits=5, decimal_places=2, default=0)
    total_winnings = models.DecimalField(_('Gains totaux'), max_digits=12, decimal_places=2, default=0)
    
    # Période
    period_start = models.DateField(_('Début de période'))
    period_end = models.DateField(_('Fin de période'))
    
    created_at = models.DateTimeField(_('Créé le'), auto_now_add=True)
    updated_at = models.DateTimeField(_('Modifié le'), auto_now=True)
    
    class Meta:
        db_table = 'leaderboards'
        verbose_name = _('Classement')
        verbose_name_plural = _('Classements')
        ordering = ['rank']
        indexes = [
            models.Index(fields=['leaderboard_type', 'rank']),
            models.Index(fields=['game_type', 'rank']),
            models.Index(fields=['user', 'leaderboard_type']),
        ]
    
    def __str__(self):
        return f"#{self.rank} {self.user.username} ({self.get_leaderboard_type_display()})"