# apps/games/game_logic/checkers.py
# ====================================

from typing import List, Tuple, Optional, Dict, Set
from dataclasses import dataclass
from enum import Enum
import copy


class PieceType(Enum):
    """Types de pièces pour les dames."""
    MAN = 'man'      # Pion simple
    KING = 'king'    # Dame (roi)


class Color(Enum):
    """Couleurs des joueurs."""
    RED = 'red'      # Rouge (joueur 1)
    BLACK = 'black'  # Noir (joueur 2)


@dataclass
class Position:
    """Position sur le damier."""
    row: int
    col: int
    
    def __str__(self):
        return f"({self.row}, {self.col})"
    
    def is_valid(self) -> bool:
        """Vérifier si la position est valide."""
        return 0 <= self.row < 8 and 0 <= self.col < 8
    
    def is_dark_square(self) -> bool:
        """Vérifier si c'est une case sombre (jouable)."""
        return (self.row + self.col) % 2 == 1
    
    def __eq__(self, other):
        return isinstance(other, Position) and self.row == other.row and self.col == other.col
    
    def __hash__(self):
        return hash((self.row, self.col))


@dataclass
class CheckersPiece:
    """Pièce de dames."""
    piece_type: PieceType
    color: Color
    
    def __str__(self):
        """Représentation textuelle."""
        if self.color == Color.RED:
            return 'R' if self.piece_type == PieceType.MAN else 'RK'
        else:
            return 'B' if self.piece_type == PieceType.MAN else 'BK'
    
    def can_move_backward(self) -> bool:
        """Vérifier si la pièce peut reculer."""
        return self.piece_type == PieceType.KING
    
    def get_move_directions(self) -> List[Tuple[int, int]]:
        """Obtenir les directions de mouvement possibles."""
        if self.piece_type == PieceType.KING:
            # Les dames peuvent bouger dans toutes les directions
            return [(-1, -1), (-1, 1), (1, -1), (1, 1)]
        else:
            # Les pions ne peuvent avancer que vers l'avant
            if self.color == Color.RED:
                return [(-1, -1), (-1, 1)]  # Vers le haut
            else:
                return [(1, -1), (1, 1)]    # Vers le bas


@dataclass
class Move:
    """Mouvement dans les dames."""
    from_pos: Position
    to_pos: Position
    captured_pieces: List[Position]
    is_promotion: bool = False
    
    def __str__(self):
        capture_str = f" captures {self.captured_pieces}" if self.captured_pieces else ""
        promotion_str = " (promotion)" if self.is_promotion else ""
        return f"{self.from_pos} -> {self.to_pos}{capture_str}{promotion_str}"
    
    def is_capture(self) -> bool:
        """Vérifier si c'est un mouvement de capture."""
        return len(self.captured_pieces) > 0


class CheckersBoard:
    """Plateau de dames."""
    
    def __init__(self):
        self.board: List[List[Optional[CheckersPiece]]] = [[None for _ in range(8)] for _ in range(8)]
        self.current_player = Color.RED
        self.move_history: List[Move] = []
        self.mandatory_capture_piece: Optional[Position] = None
        
        self._setup_initial_position()
    
    def _setup_initial_position(self):
        """Placer les pièces en position initiale."""
        # Pièces noires (joueur 2) sur les 3 premières rangées
        for row in range(3):
            for col in range(8):
                if (row + col) % 2 == 1:  # Cases sombres seulement
                    self.board[row][col] = CheckersPiece(PieceType.MAN, Color.BLACK)
        
        # Pièces rouges (joueur 1) sur les 3 dernières rangées
        for row in range(5, 8):
            for col in range(8):
                if (row + col) % 2 == 1:  # Cases sombres seulement
                    self.board[row][col] = CheckersPiece(PieceType.MAN, Color.RED)
    
    def get_piece(self, position: Position) -> Optional[CheckersPiece]:
        """Obtenir la pièce à une position."""
        if not position.is_valid():
            return None
        return self.board[position.row][position.col]
    
    def set_piece(self, position: Position, piece: Optional[CheckersPiece]):
        """Placer une pièce à une position."""
        if position.is_valid():
            self.board[position.row][position.col] = piece
    
    def get_all_pieces(self, color: Color) -> List[Tuple[Position, CheckersPiece]]:
        """Obtenir toutes les pièces d'une couleur."""
        pieces = []
        for row in range(8):
            for col in range(8):
                pos = Position(row, col)
                piece = self.get_piece(pos)
                if piece and piece.color == color:
                    pieces.append((pos, piece))
        return pieces
    
    def get_possible_moves(self, position: Position) -> List[Move]:
        """Obtenir tous les mouvements possibles pour une pièce."""
        piece = self.get_piece(position)
        if not piece:
            return []
        
        # Si une capture est obligatoire et que cette pièce n'est pas celle qui doit capturer
        if (self.mandatory_capture_piece and 
            self.mandatory_capture_piece != position):
            return []
        
        # Vérifier d'abord les captures obligatoires
        capture_moves = self._get_capture_moves(position, piece)
        if capture_moves:
            return capture_moves
        
        # Si pas de captures obligatoires, mouvements normaux
        if not self.mandatory_capture_piece:
            return self._get_normal_moves(position, piece)
        
        return []
    
    def _get_normal_moves(self, position: Position, piece: CheckersPiece) -> List[Move]:
        """Obtenir les mouvements normaux (sans capture)."""
        moves = []
        directions = piece.get_move_directions()
        
        for dr, dc in directions:
            # Pour les pions, un seul pas
            if piece.piece_type == PieceType.MAN:
                new_pos = Position(position.row + dr, position.col + dc)
                if new_pos.is_valid() and new_pos.is_dark_square():
                    if self.get_piece(new_pos) is None:
                        # Vérifier la promotion
                        is_promotion = self._check_promotion(piece, new_pos)
                        moves.append(Move(position, new_pos, [], is_promotion))
            
            # Pour les dames, plusieurs pas possibles
            else:
                for distance in range(1, 8):
                    new_pos = Position(position.row + dr * distance, position.col + dc * distance)
                    if not new_pos.is_valid() or not new_pos.is_dark_square():
                        break
                    
                    target_piece = self.get_piece(new_pos)
                    if target_piece is None:
                        moves.append(Move(position, new_pos, []))
                    else:
                        break  # Pièce bloque le chemin
        
        return moves
    
    def _get_capture_moves(self, position: Position, piece: CheckersPiece) -> List[Move]:
        """Obtenir les mouvements de capture."""
        captures = []
        directions = piece.get_move_directions()
        
        for dr, dc in directions:
            if piece.piece_type == PieceType.MAN:
                # Capture simple pour les pions
                enemy_pos = Position(position.row + dr, position.col + dc)
                landing_pos = Position(position.row + 2*dr, position.col + 2*dc)
                
                if (enemy_pos.is_valid() and landing_pos.is_valid() and
                    enemy_pos.is_dark_square() and landing_pos.is_dark_square()):
                    
                    enemy_piece = self.get_piece(enemy_pos)
                    landing_piece = self.get_piece(landing_pos)
                    
                    if (enemy_piece and enemy_piece.color != piece.color and 
                        landing_piece is None):
                        is_promotion = self._check_promotion(piece, landing_pos)
                        move = Move(position, landing_pos, [enemy_pos], is_promotion)
                        
                        # Vérifier les captures multiples
                        additional_captures = self._get_additional_captures(landing_pos, piece, [enemy_pos])
                        if additional_captures:
                            captures.extend(additional_captures)
                        else:
                            captures.append(move)
            
            else:
                # Capture pour les dames (à distance)
                captures.extend(self._get_king_captures(position, piece, dr, dc))
        
        return captures
    
    def _get_king_captures(self, position: Position, piece: CheckersPiece, dr: int, dc: int) -> List[Move]:
        """Obtenir les captures pour une dame."""
        captures = []
        
        # Chercher la première pièce ennemie dans cette direction
        for distance in range(1, 8):
            enemy_pos = Position(position.row + dr * distance, position.col + dc * distance)
            if not enemy_pos.is_valid() or not enemy_pos.is_dark_square():
                break
            
            enemy_piece = self.get_piece(enemy_pos)
            if enemy_piece:
                if enemy_piece.color != piece.color:
                    # Trouver les cases d'atterrissage possibles après la capture
                    for landing_distance in range(distance + 1, 8):
                        landing_pos = Position(
                            position.row + dr * landing_distance,
                            position.col + dc * landing_distance
                        )
                        
                        if not landing_pos.is_valid() or not landing_pos.is_dark_square():
                            break
                        
                        if self.get_piece(landing_pos) is None:
                            move = Move(position, landing_pos, [enemy_pos])
                            # Vérifier les captures multiples pour les dames
                            additional_captures = self._get_additional_captures(landing_pos, piece, [enemy_pos])
                            if additional_captures:
                                captures.extend(additional_captures)
                            else:
                                captures.append(move)
                        else:
                            break
                break
        
        return captures
    
    def _get_additional_captures(self, position: Position, piece: CheckersPiece, 
                               already_captured: List[Position]) -> List[Move]:
        """Obtenir les captures additionnelles (captures multiples)."""
        additional_moves = []
        directions = piece.get_move_directions()
        
        for dr, dc in directions:
            if piece.piece_type == PieceType.MAN:
                enemy_pos = Position(position.row + dr, position.col + dc)
                landing_pos = Position(position.row + 2*dr, position.col + 2*dc)
                
                if (enemy_pos.is_valid() and landing_pos.is_valid() and
                    enemy_pos.is_dark_square() and landing_pos.is_dark_square() and
                    enemy_pos not in already_captured):
                    
                    enemy_piece = self.get_piece(enemy_pos)
                    landing_piece = self.get_piece(landing_pos)
                    
                    if (enemy_piece and enemy_piece.color != piece.color and 
                        landing_piece is None):
                        
                        new_captured = already_captured + [enemy_pos]
                        is_promotion = self._check_promotion(piece, landing_pos)
                        
                        # Récursivement chercher plus de captures
                        further_captures = self._get_additional_captures(landing_pos, piece, new_captured)
                        if further_captures:
                            additional_moves.extend(further_captures)
                        else:
                            # Construire le mouvement final
                            original_pos = self._get_original_position(already_captured)
                            move = Move(original_pos, landing_pos, new_captured, is_promotion)
                            additional_moves.append(move)
        
        return additional_moves
    
    def _get_original_position(self, captured_pieces: List[Position]) -> Position:
        """Retrouver la position originale à partir des captures."""
        # Cette méthode est simplifiée - dans une implémentation complète,
        # il faudrait garder trace de la position de départ
        return Position(0, 0)  # Placeholder
    
    def _check_promotion(self, piece: CheckersPiece, new_position: Position) -> bool:
        """Vérifier si une pièce doit être promue."""
        if piece.piece_type == PieceType.KING:
            return False
        
        if piece.color == Color.RED and new_position.row == 0:
            return True
        elif piece.color == Color.BLACK and new_position.row == 7:
            return True
        
        return False
    
    def make_move(self, move: Move) -> bool:
        """Effectuer un mouvement."""
        piece = self.get_piece(move.from_pos)
        if not piece or piece.color != self.current_player:
            return False
        
        # Vérifier que le mouvement est légal
        possible_moves = self.get_possible_moves(move.from_pos)
        if move not in possible_moves:
            return False
        
        # Effectuer le mouvement
        self.set_piece(move.from_pos, None)
        
        # Gérer la promotion
        if move.is_promotion:
            promoted_piece = CheckersPiece(PieceType.KING, piece.color)
            self.set_piece(move.to_pos, promoted_piece)
        else:
            self.set_piece(move.to_pos, piece)
        
        # Supprimer les pièces capturées
        for captured_pos in move.captured_pieces:
            self.set_piece(captured_pos, None)
        
        # Vérifier si d'autres captures sont possibles avec la même pièce
        if move.is_capture():
            additional_captures = self._get_capture_moves(move.to_pos, 
                                                        self.get_piece(move.to_pos))
            if additional_captures:
                # La même pièce doit continuer à capturer
                self.mandatory_capture_piece = move.to_pos
            else:
                self.mandatory_capture_piece = None
                self._switch_player()
        else:
            self.mandatory_capture_piece = None
            self._switch_player()
        
        # Ajouter à l'historique
        self.move_history.append(move)
        
        return True
    
    def _switch_player(self):
        """Changer de joueur."""
        self.current_player = Color.BLACK if self.current_player == Color.RED else Color.RED
    
    def has_mandatory_captures(self, color: Color) -> bool:
        """Vérifier s'il y a des captures obligatoires."""
        pieces = self.get_all_pieces(color)
        
        for pos, piece in pieces:
            capture_moves = self._get_capture_moves(pos, piece)
            if capture_moves:
                return True
        
        return False
    
    def get_all_legal_moves(self, color: Color) -> List[Tuple[Position, List[Move]]]:
        """Obtenir tous les mouvements légaux pour une couleur."""
        legal_moves = []
        pieces = self.get_all_pieces(color)
        
        # Vérifier les captures obligatoires d'abord
        has_captures = self.has_mandatory_captures(color)
        
        for pos, piece in pieces:
            if has_captures:
                # Seulement les captures si elles sont obligatoires
                moves = self._get_capture_moves(pos, piece)
            else:
                # Tous les mouvements possibles
                moves = self.get_possible_moves(pos)
            
            if moves:
                legal_moves.append((pos, moves))
        
        return legal_moves
    
    def is_game_over(self) -> bool:
        """Vérifier si le jeu est terminé."""
        return self.get_winner() is not None
    
    def get_winner(self) -> Optional[Color]:
        """Obtenir le gagnant."""
        red_pieces = self.get_all_pieces(Color.RED)
        black_pieces = self.get_all_pieces(Color.BLACK)
        
        # Pas de pièces = défaite
        if not red_pieces:
            return Color.BLACK
        elif not black_pieces:
            return Color.RED
        
        # Pas de mouvements légaux = défaite
        current_moves = self.get_all_legal_moves(self.current_player)
        if not current_moves:
            return Color.BLACK if self.current_player == Color.RED else Color.RED
        
        return None
    
    def count_pieces(self, color: Color) -> Dict[str, int]:
        """Compter les pièces d'une couleur."""
        pieces = self.get_all_pieces(color)
        count = {'men': 0, 'kings': 0}
        
        for _, piece in pieces:
            if piece.piece_type == PieceType.MAN:
                count['men'] += 1
            else:
                count['kings'] += 1
        
        return count
    
    def to_dict(self) -> dict:
        """Convertir l'état du plateau en dictionnaire."""
        board_state = []
        for row in range(8):
            board_row = []
            for col in range(8):
                piece = self.board[row][col]
                if piece:
                    board_row.append({
                        'type': piece.piece_type.value,
                        'color': piece.color.value
                    })
                else:
                    board_row.append(None)
            board_state.append(board_row)
        
        return {
            'board': board_state,
            'current_player': self.current_player.value,
            'mandatory_capture_piece': {
                'row': self.mandatory_capture_piece.row,
                'col': self.mandatory_capture_piece.col
            } if self.mandatory_capture_piece else None,
            'move_history': [str(move) for move in self.move_history],
            'piece_counts': {
                'red': self.count_pieces(Color.RED),
                'black': self.count_pieces(Color.BLACK)
            }
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'CheckersBoard':
        """Créer un plateau depuis un dictionnaire."""
        board = cls.__new__(cls)
        board.board = [[None for _ in range(8)] for _ in range(8)]
        
        # Restaurer les pièces
        for row in range(8):
            for col in range(8):
                piece_data = data['board'][row][col]
                if piece_data:
                    piece_type = PieceType(piece_data['type'])
                    color = Color(piece_data['color'])
                    board.board[row][col] = CheckersPiece(piece_type, color)
        
        # Restaurer l'état
        board.current_player = Color(data['current_player'])
        
        if data['mandatory_capture_piece']:
            board.mandatory_capture_piece = Position(
                data['mandatory_capture_piece']['row'],
                data['mandatory_capture_piece']['col']
            )
        else:
            board.mandatory_capture_piece = None
        
        board.move_history = []  # Simplification
        
        return board


class CheckersGameEngine:
    """Moteur de jeu de dames pour RUMO RUSH."""
    
    def __init__(self):
        self.board = CheckersBoard()
    
    def get_game_state(self) -> dict:
        """Obtenir l'état complet du jeu."""
        state = self.board.to_dict()
        
        # Ajouter des informations de jeu
        current_color = self.board.current_player
        
        state.update({
            'status': self._get_game_status(),
            'legal_moves': self._get_legal_moves_dict(current_color),
            'has_mandatory_captures': self.board.has_mandatory_captures(current_color),
            'game_result': self._get_game_result()
        })
        
        return state
    
    def make_move_from_dict(self, move_data: dict) -> tuple[bool, str]:
        """Effectuer un mouvement depuis un dictionnaire."""
        try:
            from_square = move_data.get('from')
            to_square = move_data.get('to')
            
            if not from_square or not to_square:
                return False, "Cases de départ et d'arrivée requises"
            
            from_pos = Position(from_square['row'], from_square['col'])
            to_pos = Position(to_square['row'], to_square['col'])
            
            # Trouver le mouvement correspondant
            possible_moves = self.board.get_possible_moves(from_pos)
            
            for move in possible_moves:
                if move.to_pos == to_pos:
                    if self.board.make_move(move):
                        return True, f"Mouvement effectué: {move}"
                    else:
                        return False, "Échec de l'exécution du mouvement"
            
            return False, "Mouvement illégal"
            
        except Exception as e:
            return False, f"Erreur: {str(e)}"
    
    def get_legal_moves_for_position(self, row: int, col: int) -> list:
        """Obtenir les mouvements légaux pour une position."""
        try:
            pos = Position(row, col)
            moves = self.board.get_possible_moves(pos)
            
            return [
                {
                    'to': {'row': move.to_pos.row, 'col': move.to_pos.col},
                    'captured': [{'row': cap.row, 'col': cap.col} for cap in move.captured_pieces],
                    'is_capture': move.is_capture(),
                    'is_promotion': move.is_promotion
                }
                for move in moves
            ]
            
        except Exception:
            return []
    
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
        elif self.board.has_mandatory_captures(self.board.current_player):
            return "mandatory_capture"
        else:
            return "playing"
    
    def _get_legal_moves_dict(self, color: Color) -> dict:
        """Obtenir tous les mouvements légaux organisés par position."""
        moves_dict = {}
        legal_moves = self.board.get_all_legal_moves(color)
        
        for pos, moves in legal_moves:
            key = f"{pos.row}_{pos.col}"
            moves_dict[key] = [
                {
                    'to': {'row': move.to_pos.row, 'col': move.to_pos.col},
                    'captured': [{'row': cap.row, 'col': cap.col} for cap in move.captured_pieces],
                    'is_capture': move.is_capture(),
                    'is_promotion': move.is_promotion
                }
                for move in moves
            ]
        
        return moves_dict
    
    def _get_game_result(self) -> Optional[dict]:
        """Obtenir le résultat du jeu."""
        if not self.board.is_game_over():
            return None
        
        winner = self.board.get_winner()
        
        if winner:
            return {
                'result': 'win',
                'winner': winner.value,
                'reason': 'opponent_eliminated'
            }
        else:
            return {
                'result': 'draw',
                'reason': 'stalemate'
            }
    
    def reset_game(self):
        """Réinitialiser le jeu."""
        self.board = CheckersBoard()
    
    def validate_move_format(self, move_data: dict) -> tuple[bool, str]:
        """Valider le format des données de mouvement."""
        required_fields = ['from', 'to']
        
        for field in required_fields:
            if field not in move_data:
                return False, f"Champ '{field}' manquant"
        
        # Valider le format des positions
        for pos_key in ['from', 'to']:
            pos_data = move_data[pos_key]
            if not isinstance(pos_data, dict) or 'row' not in pos_data or 'col' not in pos_data:
                return False, f"Format de position invalide pour '{pos_key}'"
            
            try:
                row, col = pos_data['row'], pos_data['col']
                if not (0 <= row < 8 and 0 <= col < 8):
                    return False, f"Position hors limites pour '{pos_key}'"
            except (TypeError, ValueError):
                return False, f"Coordonnées invalides pour '{pos_key}'"
        
        return True, "Format valide"


# Fonctions utilitaires pour l'intégration avec Django

def create_checkers_game() -> dict:
    """Créer une nouvelle partie de dames."""
    engine = CheckersGameEngine()
    return engine.get_game_state()

def make_checkers_move(game_data: dict, move_data: dict) -> tuple[dict, bool, str]:
    """Effectuer un mouvement dans une partie de dames."""
    try:
        # Reconstruire l'état du jeu
        engine = CheckersGameEngine()
        engine.board = CheckersBoard.from_dict(game_data)
        
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

def check_checkers_win_condition(game_data: dict) -> tuple[bool, Optional[str], str]:
    """Vérifier les conditions de victoire aux dames."""
    try:
        engine = CheckersGameEngine()
        engine.board = CheckersBoard.from_dict(game_data)
        
        if engine.is_game_over():
            winner = engine.get_winner()
            result = engine._get_game_result()
            
            if result:
                return True, winner, result['reason']
        
        return False, None, "Jeu en cours"
        
    except Exception as e:
        return False, None, f"Erreur: {str(e)}"

def get_checkers_legal_moves(game_data: dict, row: int, col: int) -> list:
    """Obtenir les mouvements légaux pour une position."""
    try:
        engine = CheckersGameEngine()
        engine.board = CheckersBoard.from_dict(game_data)
        return engine.get_legal_moves_for_position(row, col)
    except Exception:
        return []
