# apps/games/game_logic/ludo.py
# =================================

from typing import List, Tuple, Optional, Dict, Set
from dataclasses import dataclass
from enum import Enum
import random


class Color(Enum):
    """Couleurs des joueurs."""
    RED = 'red'      # Rouge (joueur 1)
    BLUE = 'blue'    # Bleu (joueur 2)
    GREEN = 'green'  # Vert (joueur 3) - pour extension 4 joueurs
    YELLOW = 'yellow' # Jaune (joueur 4) - pour extension 4 joueurs


class PieceState(Enum):
    """États des pièces."""
    HOME = 'home'        # À la maison (base)
    ACTIVE = 'active'    # Sur le plateau
    FINISHED = 'finished' # Arrivée à destination


@dataclass
class Position:
    """Position sur le plateau de Ludo."""
    square: int  # Numéro de case (0-51 pour le tour du plateau)
    is_safe: bool = False
    is_home_column: bool = False
    color_zone: Optional[Color] = None
    
    def __str__(self):
        return f"Square {self.square}" + (" (safe)" if self.is_safe else "")


@dataclass
class LudoPiece:
    """Pièce de Ludo."""
    color: Color
    piece_id: int  # 0, 1, 2, 3 pour chaque joueur
    state: PieceState
    position: Optional[Position] = None
    steps_in_home_column: int = 0  # Steps taken in the final home column
    
    def __str__(self):
        return f"{self.color.value}_{self.piece_id}"
    
    def is_at_home(self) -> bool:
        """Vérifier si la pièce est à la maison."""
        return self.state == PieceState.HOME
    
    def is_finished(self) -> bool:
        """Vérifier si la pièce est arrivée."""
        return self.state == PieceState.FINISHED
    
    def can_move(self, dice_value: int) -> bool:
        """Vérifier si la pièce peut bouger avec cette valeur de dé."""
        if self.state == PieceState.FINISHED:
            return False
        
        if self.state == PieceState.HOME:
            return dice_value == 6  # Il faut un 6 pour sortir de la maison
        
        return True


@dataclass
class Move:
    """Mouvement dans Ludo."""
    piece: LudoPiece
    dice_value: int
    from_position: Optional[Position]
    to_position: Position
    captured_pieces: List[LudoPiece]
    brings_piece_out: bool = False  # Sort une pièce de la maison
    
    def __str__(self):
        capture_str = f" captures {len(self.captured_pieces)}" if self.captured_pieces else ""
        return f"{self.piece} moves {self.dice_value} steps{capture_str}"


class LudoBoard:
    """Plateau de Ludo."""
    
    # Configuration du plateau
    BOARD_SIZE = 52
    HOME_ENTRY_SQUARES = {
        Color.RED: 1,     # Case d'entrée pour les pièces rouges
        Color.BLUE: 14,   # Case d'entrée pour les pièces bleues
        Color.GREEN: 27,  # Case d'entrée pour les pièces vertes
        Color.YELLOW: 40  # Case d'entrée pour les pièces jaunes
    }
    
    HOME_COLUMN_START = {
        Color.RED: 51,    # Case avant la colonne finale rouge
        Color.BLUE: 12,   # Case avant la colonne finale bleue
        Color.GREEN: 25,  # Case avant la colonne finale verte
        Color.YELLOW: 38  # Case avant la colonne finale jaune
    }
    
    SAFE_SQUARES = [8, 13, 21, 26, 34, 39, 47]  # Cases sûres
    
    def __init__(self, num_players: int = 2):
        self.num_players = num_players
        self.current_player = Color.RED
        self.pieces: Dict[Color, List[LudoPiece]] = {}
        self.board_squares: List[Optional[LudoPiece]] = [None] * self.BOARD_SIZE
        self.dice_history: List[int] = []
        self.move_history: List[Move] = []
        self.consecutive_sixes = 0
        self.extra_turn = False
        
        # Définir les couleurs actives selon le nombre de joueurs
        if num_players == 2:
            self.active_colors = [Color.RED, Color.BLUE]
        elif num_players == 3:
            self.active_colors = [Color.RED, Color.BLUE, Color.GREEN]
        else:
            self.active_colors = [Color.RED, Color.BLUE, Color.GREEN, Color.YELLOW]
        
        self._setup_pieces()
    
    def _setup_pieces(self):
        """Initialiser les pièces."""
        for color in self.active_colors:
            self.pieces[color] = []
            for i in range(4):  # 4 pièces par joueur
                piece = LudoPiece(color, i, PieceState.HOME)
                self.pieces[color].append(piece)
    
    def get_piece_at_square(self, square: int) -> Optional[LudoPiece]:
        """Obtenir la pièce à une case donnée."""
        if 0 <= square < self.BOARD_SIZE:
            return self.board_squares[square]
        return None
    
    def place_piece(self, piece: LudoPiece, square: int):
        """Placer une pièce sur le plateau."""
        if 0 <= square < self.BOARD_SIZE:
            self.board_squares[square] = piece
            piece.position = Position(square, square in self.SAFE_SQUARES)
            piece.state = PieceState.ACTIVE
    
    def remove_piece_from_board(self, piece: LudoPiece):
        """Retirer une pièce du plateau."""
        if piece.position and piece.position.square < self.BOARD_SIZE:
            self.board_squares[piece.position.square] = None
    
    def get_entry_square(self, color: Color) -> int:
        """Obtenir la case d'entrée pour une couleur."""
        return self.HOME_ENTRY_SQUARES[color]
    
    def get_home_column_start(self, color: Color) -> int:
        """Obtenir le début de la colonne finale."""
        return self.HOME_COLUMN_START[color]
    
    def roll_dice(self) -> int:
        """Lancer le dé."""
        dice_value = random.randint(1, 6)
        self.dice_history.append(dice_value)
        return dice_value
    
    def get_possible_moves(self, color: Color, dice_value: int) -> List[Move]:
        """Obtenir tous les mouvements possibles pour un joueur."""
        moves = []
        player_pieces = self.pieces[color]
        
        for piece in player_pieces:
            if piece.can_move(dice_value):
                move = self._calculate_move(piece, dice_value)
                if move:
                    moves.append(move)
        
        return moves
    
    def _calculate_move(self, piece: LudoPiece, dice_value: int) -> Optional[Move]:
        """Calculer un mouvement pour une pièce."""
        if piece.state == PieceState.FINISHED:
            return None
        
        captured_pieces = []
        
        if piece.state == PieceState.HOME:
            # Sortir de la maison (nécessite un 6)
            if dice_value == 6:
                entry_square = self.get_entry_square(piece.color)
                target_piece = self.get_piece_at_square(entry_square)
                
                if target_piece and target_piece.color != piece.color:
                    captured_pieces.append(target_piece)
                elif target_piece and target_piece.color == piece.color:
                    return None  # Case occupée par une pièce alliée
                
                return Move(
                    piece=piece,
                    dice_value=dice_value,
                    from_position=None,
                    to_position=Position(entry_square, entry_square in self.SAFE_SQUARES),
                    captured_pieces=captured_pieces,
                    brings_piece_out=True
                )
            else:
                return None
        
        elif piece.state == PieceState.ACTIVE:
            current_square = piece.position.square
            
            # Vérifier si la pièce entre dans sa colonne finale
            home_column_start = self.get_home_column_start(piece.color)
            
            if current_square <= home_column_start < current_square + dice_value:
                # La pièce entre dans la colonne finale
                steps_in_column = (current_square + dice_value) - home_column_start - 1
                
                if steps_in_column <= 5:  # Maximum 5 cases dans la colonne finale
                    if steps_in_column == 5:
                        # Pièce arrive à destination
                        return Move(
                            piece=piece,
                            dice_value=dice_value,
                            from_position=piece.position,
                            to_position=Position(-1, is_home_column=True),  # Position spéciale pour "fini"
                            captured_pieces=[]
                        )
                    else:
                        # Pièce avance dans la colonne finale
                        return Move(
                            piece=piece,
                            dice_value=dice_value,
                            from_position=piece.position,
                            to_position=Position(-1, is_home_column=True),
                            captured_pieces=[]
                        )
                else:
                    return None  # Dépassement de la zone finale
            
            else:
                # Mouvement normal sur le plateau
                target_square = (current_square + dice_value) % self.BOARD_SIZE
                target_piece = self.get_piece_at_square(target_square)
                
                # Vérifier les captures
                if target_piece:
                    if target_piece.color != piece.color:
                        # Case sûre : pas de capture possible
                        if target_square in self.SAFE_SQUARES:
                            return None
                        captured_pieces.append(target_piece)
                    else:
                        return None  # Case occupée par pièce alliée
                
                return Move(
                    piece=piece,
                    dice_value=dice_value,
                    from_position=piece.position,
                    to_position=Position(target_square, target_square in self.SAFE_SQUARES),
                    captured_pieces=captured_pieces
                )
        
        return None
    
    def make_move(self, move: Move) -> bool:
        """Effectuer un mouvement."""
        try:
            piece = move.piece
            
            # Retirer la pièce de sa position actuelle
            if piece.state == PieceState.ACTIVE and piece.position:
                self.remove_piece_from_board(piece)
            
            # Gérer les captures
            for captured_piece in move.captured_pieces:
                self.remove_piece_from_board(captured_piece)
                captured_piece.state = PieceState.HOME
                captured_piece.position = None
            
            # Placer la pièce à sa nouvelle position
            if move.to_position.is_home_column:
                # Pièce dans la colonne finale ou finie
                if move.to_position.square == -1:
                    steps_from_home_start = move.dice_value
                    if piece.position:
                        home_start = self.get_home_column_start(piece.color)
                        steps_from_home_start = (piece.position.square + move.dice_value) - home_start - 1
                    
                    piece.steps_in_home_column = steps_from_home_start
                    
                    if steps_from_home_start >= 5:
                        piece.state = PieceState.FINISHED
                    else:
                        piece.state = PieceState.ACTIVE
                    
                    piece.position = move.to_position
            else:
                # Mouvement normal
                self.place_piece(piece, move.to_position.square)
            
            # Ajouter à l'historique
            self.move_history.append(move)
            
            return True
            
        except Exception as e:
            return False
    
    def has_legal_moves(self, color: Color, dice_value: int) -> bool:
        """Vérifier si un joueur a des mouvements légaux."""
        return len(self.get_possible_moves(color, dice_value)) > 0
    
    def get_winner(self) -> Optional[Color]:
        """Obtenir le gagnant (toutes les pièces finies)."""
        for color in self.active_colors:
            finished_pieces = sum(1 for piece in self.pieces[color] if piece.is_finished())
            if finished_pieces == 4:
                return color
        return None
    
    def is_game_over(self) -> bool:
        """Vérifier si le jeu est terminé."""
        return self.get_winner() is not None
    
    def get_next_player(self) -> Color:
        """Obtenir le prochain joueur."""
        current_index = self.active_colors.index(self.current_player)
        next_index = (current_index + 1) % len(self.active_colors)
        return self.active_colors[next_index]
    
    def switch_turn(self, dice_value: int):
        """Changer de tour selon les règles du Ludo."""
        if dice_value == 6:
            self.consecutive_sixes += 1
            if self.consecutive_sixes >= 3:
                # Trois 6 consécutifs : passer le tour
                self.consecutive_sixes = 0
                self.current_player = self.get_next_player()
            # Sinon, le joueur rejoue
        else:
            self.consecutive_sixes = 0
            self.current_player = self.get_next_player()
    
    def get_piece_counts(self) -> Dict[Color, Dict[str, int]]:
        """Obtenir le décompte des pièces par état."""
        counts = {}
        for color in self.active_colors:
            counts[color] = {
                'home': sum(1 for piece in self.pieces[color] if piece.is_at_home()),
                'active': sum(1 for piece in self.pieces[color] if piece.state == PieceState.ACTIVE),
                'finished': sum(1 for piece in self.pieces[color] if piece.is_finished())
            }
        return counts
    
    def to_dict(self) -> dict:
        """Convertir l'état du plateau en dictionnaire."""
        # Convertir l'état des pièces
        pieces_state = {}
        for color, pieces in self.pieces.items():
            pieces_state[color.value] = []
            for piece in pieces:
                piece_data = {
                    'piece_id': piece.piece_id,
                    'state': piece.state.value,
                    'steps_in_home_column': piece.steps_in_home_column
                }
                
                if piece.position:
                    piece_data['position'] = {
                        'square': piece.position.square,
                        'is_safe': piece.position.is_safe,
                        'is_home_column': piece.position.is_home_column
                    }
                else:
                    piece_data['position'] = None
                
                pieces_state[color.value].append(piece_data)
        
        # État du plateau
        board_state = []
        for i, piece in enumerate(self.board_squares):
            if piece:
                board_state.append({
                    'square': i,
                    'piece': f"{piece.color.value}_{piece.piece_id}"
                })
        
        return {
            'pieces': pieces_state,
            'board': board_state,
            'current_player': self.current_player.value,
            'active_colors': [color.value for color in self.active_colors],
            'dice_history': self.dice_history[-10:],  # Garder les 10 derniers lancers
            'consecutive_sixes': self.consecutive_sixes,
            'piece_counts': {
                color.value: self.get_piece_counts()[color]
                for color in self.active_colors
            },
            'move_count': len(self.move_history)
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'LudoBoard':
        """Créer un plateau depuis un dictionnaire."""
        # Déterminer le nombre de joueurs
        active_colors = [Color(color) for color in data['active_colors']]
        board = cls(len(active_colors))
        
        # Restaurer l'état des pièces
        for color_name, pieces_data in data['pieces'].items():
            color = Color(color_name)
            for i, piece_data in enumerate(pieces_data):
                piece = board.pieces[color][i]
                piece.state = PieceState(piece_data['state'])
                piece.steps_in_home_column = piece_data['steps_in_home_column']
                
                if piece_data['position']:
                    pos_data = piece_data['position']
                    piece.position = Position(
                        square=pos_data['square'],
                        is_safe=pos_data['is_safe'],
                        is_home_column=pos_data['is_home_column']
                    )
        
        # Restaurer l'état du plateau
        board.board_squares = [None] * board.BOARD_SIZE
        for square_data in data['board']:
            square = square_data['square']
            piece_id = square_data['piece']
            color_name, piece_num = piece_id.split('_')
            color = Color(color_name)
            piece = board.pieces[color][int(piece_num)]
            board.board_squares[square] = piece
        
        # Restaurer les autres états
        board.current_player = Color(data['current_player'])
        board.consecutive_sixes = data['consecutive_sixes']
        board.dice_history = data['dice_history']
        
        return board


class LudoGameEngine:
    """Moteur de jeu Ludo pour RUMO RUSH."""
    
    def __init__(self, num_players: int = 2):
        self.board = LudoBoard(num_players)
        self.current_dice_value = 0
        self.must_move = False  # Force le joueur à bouger après avoir lancé le dé
    
    def get_game_state(self) -> dict:
        """Obtenir l'état complet du jeu."""
        state = self.board.to_dict()
        
        # Ajouter des informations de jeu
        state.update({
            'status': self._get_game_status(),
            'current_dice_value': self.current_dice_value,
            'must_move': self.must_move,
            'can_roll_dice': not self.must_move,
            'legal_moves': self._get_legal_moves_for_current_player(),
            'game_result': self._get_game_result()
        })
        
        return state
    
    def roll_dice(self) -> tuple[bool, str, int]:
        """Lancer le dé."""
        if self.must_move:
            return False, "Vous devez d'abord effectuer un mouvement", 0
        
        if self.board.is_game_over():
            return False, "Le jeu est terminé", 0
        
        dice_value = self.board.roll_dice()
        self.current_dice_value = dice_value
        self.must_move = True
        
        # Vérifier si le joueur peut bouger
        if not self.board.has_legal_moves(self.board.current_player, dice_value):
            # Pas de mouvement possible, passer le tour
            self._end_turn(dice_value)
            return True, f"Dé: {dice_value}. Aucun mouvement possible, tour passé.", dice_value
        
        return True, f"Dé: {dice_value}. Choisissez votre mouvement.", dice_value
    
    def make_move_from_dict(self, move_data: dict) -> tuple[bool, str]:
        """Effectuer un mouvement depuis un dictionnaire."""
        try:
            if not self.must_move:
                return False, "Vous devez d'abord lancer le dé"
            
            piece_id = move_data.get('piece_id')
            if piece_id is None:
                return False, "ID de pièce manquant"
            
            # Trouver la pièce
            player_pieces = self.board.pieces[self.board.current_player]
            if piece_id < 0 or piece_id >= len(player_pieces):
                return False, "ID de pièce invalide"
            
            piece = player_pieces[piece_id]
            
            # Calculer le mouvement
            move = self.board._calculate_move(piece, self.current_dice_value)
            if not move:
                return False, "Mouvement impossible avec cette pièce"
            
            # Effectuer le mouvement
            if self.board.make_move(move):
                capture_msg = f" et capture {len(move.captured_pieces)} pièce(s)" if move.captured_pieces else ""
                success_msg = f"Pièce {piece_id} déplacée{capture_msg}"
                
                self._end_turn(self.current_dice_value)
                return True, success_msg
            else:
                return False, "Échec de l'exécution du mouvement"
            
        except Exception as e:
            return False, f"Erreur: {str(e)}"
    
    def _end_turn(self, dice_value: int):
        """Terminer le tour actuel."""
        self.must_move = False
        self.current_dice_value = 0
        self.board.switch_turn(dice_value)
    
    def get_legal_moves_for_piece(self, piece_id: int) -> Optional[dict]:
        """Obtenir le mouvement légal pour une pièce spécifique."""
        try:
            if not self.must_move:
                return None
            
            player_pieces = self.board.pieces[self.board.current_player]
            if piece_id < 0 or piece_id >= len(player_pieces):
                return None
            
            piece = player_pieces[piece_id]
            move = self.board._calculate_move(piece, self.current_dice_value)
            
            if move:
                return {
                    'piece_id': piece_id,
                    'from_state': piece.state.value,
                    'to_position': {
                        'square': move.to_position.square,
                        'is_safe': move.to_position.is_safe,
                        'is_home_column': move.to_position.is_home_column
                    } if move.to_position.square >= 0 else None,
                    'captures': len(move.captured_pieces),
                    'brings_piece_out': move.brings_piece_out
                }
            
            return None
            
        except Exception:
            return None
    
    def is_game_over(self) -> bool:
        """Vérifier si le jeu est terminé."""
        return self.board.is_game_over()
    
    def get_winner(self) -> Optional[str]:
        """Obtenir le gagnant si le jeu est terminé."""
        winner = self.board.get_winner()
        return winner.value if winner else None
    
    def _get_game_status(self) -> str:
        """Obtenir le statut du jeu."""
        if self.board.is_game_over():
            winner = self.board.get_winner()
            return f"finished_{winner.value}" if winner else "finished_draw"
        elif self.must_move:
            return "waiting_for_move"
        else:
            return "waiting_for_dice"
    
    def _get_legal_moves_for_current_player(self) -> List[dict]:
        """Obtenir tous les mouvements légaux pour le joueur actuel."""
        if not self.must_move:
            return []
        
        legal_moves = []
        player_pieces = self.board.pieces[self.board.current_player]
        
        for i, piece in enumerate(player_pieces):
            move_info = self.get_legal_moves_for_piece(i)
            if move_info:
                legal_moves.append(move_info)
        
        return legal_moves
    
    def _get_game_result(self) -> Optional[dict]:
        """Obtenir le résultat du jeu."""
        if not self.board.is_game_over():
            return None
        
        winner = self.board.get_winner()
        
        if winner:
            return {
                'result': 'win',
                'winner': winner.value,
                'reason': 'all_pieces_finished'
            }
        
        return {
            'result': 'draw',
            'reason': 'stalemate'
        }
    
    def reset_game(self):
        """Réinitialiser le jeu."""
        num_players = len(self.board.active_colors)
        self.board = LudoBoard(num_players)
        self.current_dice_value = 0
        self.must_move = False
    
    def validate_move_format(self, move_data: dict) -> tuple[bool, str]:
        """Valider le format des données de mouvement."""
        if 'piece_id' not in move_data:
            return False, "Champ 'piece_id' manquant"
        
        try:
            piece_id = int(move_data['piece_id'])
            if piece_id < 0 or piece_id > 3:
                return False, "piece_id doit être entre 0 et 3"
        except (TypeError, ValueError):
            return False, "piece_id doit être un entier"
        
        return True, "Format valide"
    
    def get_game_statistics(self) -> dict:
        """Obtenir les statistiques du jeu."""
        piece_counts = self.board.get_piece_counts()
        
        return {
            'moves_played': len(self.board.move_history),
            'dice_rolls': len(self.board.dice_history),
            'average_dice': sum(self.board.dice_history) / len(self.board.dice_history) if self.board.dice_history else 0,
            'piece_counts': {
                color.value: counts for color, counts in piece_counts.items()
            },
            'current_turn': self.board.current_player.value,
            'consecutive_sixes': self.board.consecutive_sixes
        }


# Fonctions utilitaires pour l'intégration avec Django

def create_ludo_game(num_players: int = 2) -> dict:
    """Créer une nouvelle partie de Ludo."""
    engine = LudoGameEngine(num_players)
    return engine.get_game_state()

def make_ludo_move(game_data: dict, move_data: dict) -> tuple[dict, bool, str]:
    """Effectuer un mouvement dans une partie de Ludo."""
    try:
        # Reconstruire l'état du jeu
        engine = LudoGameEngine()
        engine.board = LudoBoard.from_dict(game_data)
        engine.current_dice_value = game_data.get('current_dice_value', 0)
        engine.must_move = game_data.get('must_move', False)
        
        # Valider le format du mouvement
        is_valid, message = engine.validate_move_format(move_data)
        if not is_valid:
            return game_data, False, message
        
        # Effectuer le mouvement
        success, message = engine.make_move_from_dict(move_data)
        
        # Retourner l'état mis à jour
        new_game_state = engine.get_game_state()
        return new_game_state, success, message
        
    except Exception as e:
        return game_data, False, f"Erreur interne: {str(e)}"

def roll_ludo_dice(game_data: dict) -> tuple[dict, bool, str, int]:
    """Lancer le dé dans une partie de Ludo."""
    try:
        # Reconstruire l'état du jeu
        engine = LudoGameEngine()
        engine.board = LudoBoard.from_dict(game_data)
        engine.current_dice_value = game_data.get('current_dice_value', 0)
        engine.must_move = game_data.get('must_move', False)
        
        # Lancer le dé
        success, message, dice_value = engine.roll_dice()
        
        # Retourner l'état mis à jour
        new_game_state = engine.get_game_state()
        return new_game_state, success, message, dice_value
        
    except Exception as e:
        return game_data, False, f"Erreur interne: {str(e)}", 0

def check_ludo_win_condition(game_data: dict) -> tuple[bool, Optional[str], str]:
    """Vérifier les conditions de victoire au Ludo."""
    try:
        engine = LudoGameEngine()
        engine.board = LudoBoard.from_dict(game_data)
        
        if engine.is_game_over():
            winner = engine.get_winner()
            result = engine._get_game_result()
            
            if result:
                return True, winner, result['reason']
        
        return False, None, "Jeu en cours"
        
    except Exception as e:
        return False, None, f"Erreur: {str(e)}"

def get_ludo_legal_moves(game_data: dict) -> list:
    """Obtenir les mouvements légaux pour le joueur actuel."""
    try:
        engine = LudoGameEngine()
        engine.board = LudoBoard.from_dict(game_data)
        engine.current_dice_value = game_data.get('current_dice_value', 0)
        engine.must_move = game_data.get('must_move', False)
        
        return engine._get_legal_moves_for_current_player()
    except Exception:
        return []
