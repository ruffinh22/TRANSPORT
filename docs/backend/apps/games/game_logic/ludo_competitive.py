# apps/games/game_logic/ludo_competitive.py
# ==========================================
"""
Système compétitif pour Ludo avec timer et scoring.

RÈGLES SPÉCIALES IMPLÉMENTÉES:
================================

1. CAPTURE EN ARRIÈRE ✅
   - Un pion peut capturer en avant OU en arrière
   - Vérification de position EXACTE uniquement

2. MUR AU PORTAIL (2 pions) 🚧
   - 2 pions de même couleur au portail (sortie maison) = MUR
   - Le mur bloque le passage de l'adversaire
   - Positions de portail: 0 (rouge), 13 (vert), 26 (jaune), 39 (bleu)

3. PIONS EMPILÉS CAPTURABLES ⚔️
   - Plusieurs pions de même couleur sur une case normale peuvent être capturés ensemble
   - Exception: Les murs au portail (2+ pions) NE peuvent PAS être capturés

4. CAPTURE → PIONS RESTENT CHEZ L'ADVERSAIRE 🏠
   - Les pions capturés vont à la BASE de celui qui a capturé
   - Conceptuellement: le pion est "prisonnier" chez l'adversaire

5. CASSER UN MUR 💥
   Pour casser un mur (2 pions alignés au portail):
   - Il faut faire DEUX 6 consécutifs
   - Le dé actuel doit faire tomber EXACTEMENT sur la case du mur
   - Sans ces conditions → capture impossible, passage bloqué

6. POSITIONS DE SÉCURITÉ 🛡️
   - Cases AVANT l'entrée du couloir final (10, 23, 36, 49)
   - Aucune capture possible sur ces cases
"""

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Dict
import logging

logger = logging.getLogger(__name__)


@dataclass
class LudoTimer:
    """Timer pour le Ludo compétitif - supporte n'importe quelles couleurs."""
    move_time_limit: int = 120  # 120 secondes par coup
    global_time_limit: int = 21000  # 5 heures 50 minutes (21000s) par joueur
    
    # Dictionnaire dynamique pour supporter n'importe quelles couleurs
    player_times: Dict[str, float] = field(default_factory=lambda: {})
    move_time_remaining: float = 120.0
    
    current_player: str = 'red'  # Couleur du joueur actuel
    turn_order: list = field(default_factory=lambda: ['red', 'blue'])  # Ordre des tours
    current_move_start: Optional[str] = None
    game_start_time: Optional[str] = None
    
    global_timeout: bool = False
    move_timeout: bool = False
    
    def start_game(self):
        """Démarrer le timer du jeu."""
        now = datetime.now(timezone.utc).isoformat()
        self.game_start_time = now
        self.start_move()
    
    def start_move(self):
        """Démarrer le timer pour un coup."""
        self.current_move_start = datetime.now(timezone.utc).isoformat()
        self.move_time_remaining = self.move_time_limit
        self.move_timeout = False
        # ⚠️ NE PAS réinitialiser global_timeout ici - il doit rester True une fois le temps global épuisé
        logger.info(f"⏰ Move timer started for {self.current_player} - {self.move_time_limit}s")
    
    def update(self):
        """Alias pour update_times() - pour compatibilité."""
        self.update_times()
    
    def update_times(self):
        """Mettre à jour les temps restants."""
        if not self.current_move_start:
            return
        
        now = datetime.now(timezone.utc)
        move_start = datetime.fromisoformat(self.current_move_start.replace('Z', '+00:00'))
        elapsed = (now - move_start).total_seconds()
        
        # Mettre à jour le temps du coup
        self.move_time_remaining = max(0, self.move_time_limit - elapsed)
        
        # ⚠️ Vérifier le temps global
        # On ne déduit PAS ici (déduction faite dans switch_player)
        # On vérifie juste si le joueur a déjà épuisé son temps global
        if self.current_player in self.player_times:
            # Vérifier le temps ACTUEL du joueur (déjà déduit des tours précédents)
            if self.player_times[self.current_player] <= 0:
                if not self.global_timeout:
                    logger.warning(f"⏰ GLOBAL TIMEOUT: {self.current_player} has {self.player_times[self.current_player]:.1f}s left")
                    self.global_timeout = True
        
        # Vérifier timeout du coup (120s)
        if self.move_time_remaining <= 0:
            if not self.move_timeout:
                logger.warning(f"⏰ MOVE TIMEOUT: {self.current_player} exceeded {self.move_time_limit}s")
                self.move_timeout = True
    
    def is_global_timeout(self) -> bool:
        """Vérifier si le temps global est écoulé."""
        self.update_times()
        logger.info(f"🔍 is_global_timeout check: global_timeout={self.global_timeout}, player_times={self.player_times}")
        return self.global_timeout
    
    def is_move_timeout(self) -> bool:
        """Vérifier si le timeout du coup est écoulé."""
        self.update_times()
        return self.move_timeout
    
    def switch_player(self):
        """Changer de joueur actif - supporte n'importe quelles couleurs."""
        # Déduire le temps écoulé du joueur actuel (UNE SEULE FOIS par tour)
        if self.current_move_start and self.current_player in self.player_times:
            now = datetime.now(timezone.utc)
            move_start = datetime.fromisoformat(self.current_move_start.replace('Z', '+00:00'))
            elapsed = (now - move_start).total_seconds()
            
            old_time = self.player_times[self.current_player]
            self.player_times[self.current_player] = max(0, old_time - elapsed)
            new_time = self.player_times[self.current_player]
            
            logger.info(f"⏰ {self.current_player} used {elapsed:.1f}s this turn: {old_time:.1f}s -> {new_time:.1f}s remaining")
            
            # Vérifier si ce joueur a épuisé son temps global après cette déduction
            if new_time <= 0 and old_time > 0:
                logger.warning(f"⚠️ {self.current_player} has EXHAUSTED their global time! Game should end.")
                self.global_timeout = True
        
        # Changer de joueur selon turn_order (supporte green, blue, yellow, etc.)
        try:
            current_idx = self.turn_order.index(self.current_player)
            next_idx = (current_idx + 1) % len(self.turn_order)
            self.current_player = self.turn_order[next_idx]
            logger.info(f"⏰ Timer switched from {self.turn_order[current_idx]} to {self.current_player}")
        except (ValueError, IndexError):
            # Fallback au premier joueur si erreur
            self.current_player = self.turn_order[0] if self.turn_order else 'red'
            logger.warning(f"⏰ Timer switch fallback to {self.current_player}")
        
        # Démarrer le chronomètre pour le nouveau joueur
        self.start_move()
    
    def to_dict(self) -> dict:
        """Convertir en dictionnaire."""
        self.update_times()
        return {
            'move_time_limit': self.move_time_limit,
            'global_time_limit': self.global_time_limit,
            'player_times': self.player_times,  # Dictionnaire dynamique pour toutes les couleurs
            'move_time_remaining': self.move_time_remaining,
            'current_player': self.current_player,
            'turn_order': self.turn_order,
            'current_move_start': self.current_move_start,
            'game_start_time': self.game_start_time,
            'global_timeout': self.global_timeout,
            'move_timeout': self.move_timeout
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'LudoTimer':
        """Créer depuis un dictionnaire - supporte l'ancien format et le nouveau."""
        # Support de l'ancien format avec red_time_remaining et blue_time_remaining
        player_times = data.get('player_times', {})
        if not player_times:
            # Migration de l'ancien format
            player_times = {}
            if 'red_time_remaining' in data:
                player_times['red'] = data['red_time_remaining']
            if 'blue_time_remaining' in data:
                player_times['blue'] = data['blue_time_remaining']
            if 'green_time_remaining' in data:
                player_times['green'] = data['green_time_remaining']
            if 'yellow_time_remaining' in data:
                player_times['yellow'] = data['yellow_time_remaining']
        
        # Récupérer turn_order depuis data ou construire à partir de player_times
        turn_order = data.get('turn_order', list(player_times.keys()) if player_times else ['red', 'blue'])
        
        # Si player_times est toujours vide, l'initialiser avec turn_order
        if not player_times:
            global_time_limit = data.get('global_time_limit', 21000)
            player_times = {color: float(global_time_limit) for color in turn_order}
            logger.info(f"⏰ Initialized player_times for colors: {list(player_times.keys())}")
        
        timer = cls(
            move_time_limit=data.get('move_time_limit', 120),
            global_time_limit=data.get('global_time_limit', 21000),
            player_times=player_times,
            move_time_remaining=data.get('move_time_remaining', 120.0),
            current_player=data.get('current_player', turn_order[0] if turn_order else 'red'),
            turn_order=turn_order,
            current_move_start=data.get('current_move_start'),
            game_start_time=data.get('game_start_time'),
            global_timeout=data.get('global_timeout', False),
            move_timeout=data.get('move_timeout', False)
        )
        return timer


@dataclass
class LudoScore:
    """Score pour un joueur au Ludo."""
    color: str  # 'red' ou 'blue'
    points: int = 0
    pieces_finished: int = 0  # Pièces arrivées à la fin
    pieces_active: int = 0  # Pièces en jeu
    pieces_captured: int = 0  # Pièces adverses capturées
    total_steps: int = 0  # Total des cases parcourues
    
    def to_dict(self) -> dict:
        """Convertir en dictionnaire."""
        return {
            'color': self.color,
            'points': self.points,
            'pieces_finished': self.pieces_finished,
            'pieces_active': self.pieces_active,
            'pieces_captured': self.pieces_captured,
            'total_steps': self.total_steps
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'LudoScore':
        """Créer depuis un dictionnaire."""
        return cls(
            color=data.get('color', 'red'),
            points=data.get('points', 0),
            pieces_finished=data.get('pieces_finished', 0),
            pieces_active=data.get('pieces_active', 0),
            pieces_captured=data.get('pieces_captured', 0),
            total_steps=data.get('total_steps', 0)
        )


# Système de points Ludo
LUDO_POINTS = {
    'piece_finished': 10,  # Une pièce arrive à la fin
    'piece_captured': 5,   # Capturer une pièce adverse
    'piece_out': 2,        # Sortir une pièce de la base
    'step': 0.1,           # Chaque case parcourue
}


def create_competitive_ludo_game() -> dict:
    """Créer une nouvelle partie de Ludo compétitive."""
    from apps.games.game_logic.ludo import LudoBoard, Color
    
    board = LudoBoard(num_players=2)
    
    # Créer le timer
    timer = LudoTimer()
    
    # Créer les scores
    red_score = LudoScore(color='red')
    blue_score = LudoScore(color='blue')
    
    # Créer l'état du jeu
    game_state = board.to_dict()
    game_state['timer'] = timer.to_dict()
    game_state['red_score'] = red_score.to_dict()
    game_state['blue_score'] = blue_score.to_dict()
    game_state['is_game_over'] = False
    game_state['winner'] = None
    
    logger.info("✅ Competitive Ludo game created")
    return game_state


def update_score_for_action(score: LudoScore, action: str, value: int = 1):
    """
    Mettre à jour le score selon l'action.
    
    Actions possibles:
    - 'piece_finished': Une pièce arrive à la fin
    - 'piece_captured': Capturer une pièce adverse
    - 'piece_out': Sortir une pièce de la base
    - 'step': Avancer d'une case
    """
    if action == 'piece_finished':
        score.pieces_finished += value
        score.points += LUDO_POINTS['piece_finished'] * value
    elif action == 'piece_captured':
        score.pieces_captured += value
        score.points += LUDO_POINTS['piece_captured'] * value
    elif action == 'piece_out':
        score.pieces_active += value
        score.points += LUDO_POINTS['piece_out'] * value
    elif action == 'step':
        score.total_steps += value
        score.points += int(LUDO_POINTS['step'] * value)


def check_and_auto_pass_turn_if_timeout(game_state: dict) -> tuple[dict, bool]:
    """
    Vérifier si le timeout de 120s est dépassé et donner la victoire à l'adversaire.
    Retourne (new_game_state, was_timeout_triggered)
    """
    timer = LudoTimer.from_dict(game_state.get('timer', {}))
    
    if timer.is_move_timeout():
        timeout_player = timer.current_player
        turn_order = game_state.get('turn_order', ['red', 'blue'])
        
        # Trouver l'adversaire (le prochain joueur qui n'a pas fait timeout)
        try:
            current_idx = turn_order.index(timeout_player)
            next_idx = (current_idx + 1) % len(turn_order)
            winner = turn_order[next_idx]
        except (ValueError, KeyError):
            # Fallback au premier joueur qui n'est pas timeout_player
            winner = next(p for p in turn_order if p != timeout_player)
        
        logger.warning(f"⏱️ 120s TIMEOUT for {timeout_player}. {winner.upper()} WINS!")
        
        # Marquer la partie comme terminée avec victoire par timeout
        game_state['game_over'] = True
        game_state['winner'] = winner
        game_state['win_reason'] = f'timeout_{timeout_player}'
        game_state['status'] = f'finished_{winner}'
        
        # Mettre à jour le timer
        game_state['timer'] = timer.to_dict()
        
        return game_state, True
    
    return game_state, False


def check_competitive_ludo_game_over(game_state: dict) -> tuple[bool, Optional[str], dict]:
    """
    Vérifier si la partie de Ludo est terminée.
    Retourne (is_over, winner, details)
    Supporte les couleurs dynamiques (red, yellow, blue, green)
    """
    # Vérifier d'abord le timeout du coup (120s)
    timer = LudoTimer.from_dict(game_state.get('timer', {}))
    
    if timer.is_move_timeout():
        timeout_player = timer.current_player
        turn_order = game_state.get('turn_order', ['red', 'blue'])
        
        # Trouver l'adversaire
        try:
            current_idx = turn_order.index(timeout_player)
            next_idx = (current_idx + 1) % len(turn_order)
            winner = turn_order[next_idx]
        except (ValueError, KeyError):
            winner = next(p for p in turn_order if p != timeout_player)
        
        return True, winner, {
            'reason': f'timeout_{timeout_player}',
            'message': f'{timeout_player} n\'a pas joué en 120 secondes'
        }
    
    # Récupérer les couleurs actives dynamiquement
    active_colors = game_state.get('active_colors', [])
    if not active_colors:
        # Fallback: essayer de les extraire depuis player_colors
        player_colors = game_state.get('player_colors', {})
        active_colors = list(set(player_colors.values()))
    
    if len(active_colors) < 2:
        return False, None, {}
    
    # Charger les scores dynamiquement
    scores = {}
    for color in active_colors:
        score_key = f'{color}_score'
        if score_key in game_state:
            scores[color] = LudoScore.from_dict(game_state.get(score_key, {}))
    
    # Vérifier si un joueur a fini toutes ses pièces (4 pièces)
    for color, score in scores.items():
        if score.pieces_finished >= 4:
            details = {
                'reason': 'all_pieces_finished'
            }
            # Ajouter tous les scores au détail
            for c in active_colors:
                details[f'{c}_score'] = game_state.get(f'{c}_score')
            
            return True, color, details
    
    # Timeout global - gagnant selon les points
    if timer.is_global_timeout():
        # Trouver le joueur avec le PLUS de points
        winner = None
        max_points = -1
        tied_colors = []
        
        logger.info(f"⏰ Global timeout detected - comparing scores:")
        for color, score in scores.items():
            logger.info(f"   {color}: {score.points} points")
            if score.points > max_points:
                max_points = score.points
                winner = color
                tied_colors = [color]
                logger.info(f"   ✅ New leader: {color} with {max_points} points")
            elif score.points == max_points:
                tied_colors.append(color)
                logger.info(f"   ⚖️ Tied with {color} at {max_points} points")
        
        # Si égalité, c'est un match nul
        if len(tied_colors) > 1:
            winner = 'draw'
        
        details = {
            'reason': 'global_timeout'
        }
        # Ajouter tous les scores au détail
        for c in active_colors:
            details[f'{c}_score'] = game_state.get(f'{c}_score')
        
        return True, winner, details
    
    return False, None, {}
