# apps/games/game_logic/cards.py
# =================================

from typing import List, Tuple, Optional, Dict, Set
from dataclasses import dataclass
from enum import Enum
import random
import copy


class Suit(Enum):
    """Couleurs des cartes."""
    HEARTS = 'hearts'       # Cœur
    DIAMONDS = 'diamonds'   # Carreau
    CLUBS = 'clubs'         # Trèfle
    SPADES = 'spades'       # Pique


class Rank(Enum):
    """Valeurs des cartes."""
    TWO = '2'
    THREE = '3'
    FOUR = '4'
    FIVE = '5'
    SIX = '6'
    SEVEN = '7'
    EIGHT = '8'
    NINE = '9'
    TEN = '10'
    JACK = 'J'
    QUEEN = 'Q'
    KING = 'K'
    ACE = 'A'


class GameType(Enum):
    """Types de jeux de cartes disponibles."""
    RUMMY = 'rummy'         # Rami
    CRAZY_EIGHTS = 'crazy_eights'  # Huit américain
    WAR = 'war'             # Bataille


@dataclass
class Card:
    """Carte de jeu."""
    suit: Suit
    rank: Rank
    
    def __str__(self):
        return f"{self.rank.value}{self.suit.value[0].upper()}"
    
    def __eq__(self, other):
        return isinstance(other, Card) and self.suit == other.suit and self.rank == other.rank
    
    def __hash__(self):
        return hash((self.suit, self.rank))
    
    def get_value(self) -> int:
        """Obtenir la valeur numérique de la carte."""
        rank_values = {
            Rank.ACE: 1,
            Rank.TWO: 2, Rank.THREE: 3, Rank.FOUR: 4, Rank.FIVE: 5,
            Rank.SIX: 6, Rank.SEVEN: 7, Rank.EIGHT: 8, Rank.NINE: 9,
            Rank.TEN: 10, Rank.JACK: 11, Rank.QUEEN: 12, Rank.KING: 13
        }
        return rank_values[self.rank]
    
    def get_rummy_value(self) -> int:
        """Valeur pour le Rami (figures = 10, As = 1)."""
        if self.rank in [Rank.JACK, Rank.QUEEN, Rank.KING]:
            return 10
        elif self.rank == Rank.ACE:
            return 1
        else:
            return self.get_value()
    
    def can_follow(self, other_card: 'Card') -> bool:
        """Vérifier si cette carte peut suivre une autre (pour Huit américain)."""
        return self.suit == other_card.suit or self.rank == other_card.rank
    
    def is_special_card(self) -> bool:
        """Vérifier si c'est une carte spéciale (8 pour Huit américain)."""
        return self.rank == Rank.EIGHT
    
    def to_dict(self) -> dict:
        """Convertir en dictionnaire."""
        return {
            'suit': self.suit.value,
            'rank': self.rank.value
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Card':
        """Créer depuis un dictionnaire."""
        return cls(Suit(data['suit']), Rank(data['rank']))


class Deck:
    """Paquet de cartes."""
    
    def __init__(self, include_jokers: bool = False):
        self.cards: List[Card] = []
        self.include_jokers = include_jokers
        self._create_standard_deck()
        self.shuffle()
    
    def _create_standard_deck(self):
        """Créer un paquet standard de 52 cartes."""
        for suit in Suit:
            for rank in Rank:
                self.cards.append(Card(suit, rank))
    
    def shuffle(self):
        """Mélanger le paquet."""
        random.shuffle(self.cards)
    
    def deal_card(self) -> Optional[Card]:
        """Distribuer une carte."""
        return self.cards.pop() if self.cards else None
    
    def deal_hand(self, size: int) -> List[Card]:
        """Distribuer une main de cartes."""
        hand = []
        for _ in range(size):
            card = self.deal_card()
            if card:
                hand.append(card)
        return hand
    
    def size(self) -> int:
        """Nombre de cartes restantes."""
        return len(self.cards)
    
    def is_empty(self) -> bool:
        """Vérifier si le paquet est vide."""
        return len(self.cards) == 0
    
    def peek(self) -> Optional[Card]:
        """Regarder la prochaine carte sans la retirer."""
        return self.cards[-1] if self.cards else None
    
    def add_card(self, card: Card):
        """Ajouter une carte au paquet."""
        self.cards.append(card)
    
    def add_cards(self, cards: List[Card]):
        """Ajouter plusieurs cartes au paquet."""
        self.cards.extend(cards)


@dataclass
class Move:
    """Mouvement dans un jeu de cartes."""
    player_id: str
    action: str  # 'play', 'draw', 'declare', 'pass'
    cards: List[Card]
    target_suit: Optional[Suit] = None  # Pour changer la couleur (Huit américain)
    meld_type: Optional[str] = None     # Pour le Rami ('set', 'run')
    
    def __str__(self):
        if self.action == 'play':
            cards_str = ', '.join(str(card) for card in self.cards)
            return f"Play {cards_str}"
        elif self.action == 'draw':
            return "Draw card"
        elif self.action == 'declare':
            return f"Declare {self.meld_type}"
        else:
            return f"Action: {self.action}"


class CardGameBase:
    """Classe de base pour les jeux de cartes."""
    
    def __init__(self, num_players: int = 2):
        self.num_players = num_players
        self.players: List[str] = [f"player_{i+1}" for i in range(num_players)]
        self.current_player_index = 0
        self.deck = Deck()
        self.hands: Dict[str, List[Card]] = {}
        self.move_history: List[Move] = []
        self.game_over = False
        self.winner: Optional[str] = None
        
        self._setup_game()
    
    def _setup_game(self):
        """Configuration initiale du jeu."""
        # À implémenter dans les sous-classes
        pass
    
    def get_current_player(self) -> str:
        """Obtenir le joueur actuel."""
        return self.players[self.current_player_index]
    
    def next_player(self):
        """Passer au joueur suivant."""
        self.current_player_index = (self.current_player_index + 1) % self.num_players
    
    def get_hand(self, player_id: str) -> List[Card]:
        """Obtenir la main d'un joueur."""
        return self.hands.get(player_id, [])
    
    def deal_initial_hands(self, hand_size: int):
        """Distribuer les mains initiales."""
        for player in self.players:
            self.hands[player] = self.deck.deal_hand(hand_size)
    
    def is_valid_move(self, move: Move) -> bool:
        """Vérifier si un mouvement est valide."""
        # À implémenter dans les sous-classes
        return True
    
    def make_move(self, move: Move) -> bool:
        """Effectuer un mouvement."""
        if not self.is_valid_move(move):
            return False
        
        self._execute_move(move)
        self.move_history.append(move)
        self._check_win_condition()
        
        if not self.game_over:
            self.next_player()
        
        return True
    
    def _execute_move(self, move: Move):
        """Exécuter un mouvement."""
        # À implémenter dans les sous-classes
        pass
    
    def _check_win_condition(self):
        """Vérifier les conditions de victoire."""
        # À implémenter dans les sous-classes
        pass
    
    def get_possible_moves(self, player_id: str) -> List[Move]:
        """Obtenir les mouvements possibles pour un joueur."""
        # À implémenter dans les sous-classes
        return []
    
    def to_dict(self) -> dict:
        """Convertir l'état du jeu en dictionnaire."""
        hands_dict = {}
        for player, hand in self.hands.items():
            hands_dict[player] = [card.to_dict() for card in hand]
        
        return {
            'players': self.players,
            'current_player_index': self.current_player_index,
            'hands': hands_dict,
            'deck_size': self.deck.size(),
            'move_history': [str(move) for move in self.move_history],
            'game_over': self.game_over,
            'winner': self.winner
        }


class CrazyEightsGame(CardGameBase):
    """Jeu du Huit américain."""
    
    def __init__(self, num_players: int = 2):
        self.discard_pile: List[Card] = []
        self.current_suit: Optional[Suit] = None
        super().__init__(num_players)
    
    def _setup_game(self):
        """Configuration du Huit américain."""
        # Distribuer 7 cartes à chaque joueur
        self.deal_initial_hands(7)
        
        # Retourner la première carte
        first_card = self.deck.deal_card()
        if first_card:
            self.discard_pile.append(first_card)
            self.current_suit = first_card.suit
    
    def get_top_card(self) -> Optional[Card]:
        """Obtenir la carte du dessus de la pile de défausse."""
        return self.discard_pile[-1] if self.discard_pile else None
    
    def is_valid_move(self, move: Move) -> bool:
        """Vérifier si un mouvement est valide."""
        if move.action == 'draw':
            return True
        
        if move.action == 'play' and len(move.cards) == 1:
            card = move.cards[0]
            top_card = self.get_top_card()
            
            if not top_card:
                return True
            
            # Huit peut toujours être joué
            if card.is_special_card():
                return True
            
            # Vérifier si la carte peut suivre
            if self.current_suit:
                return card.suit == self.current_suit or card.rank == top_card.rank
            else:
                return card.can_follow(top_card)
        
        return False
    
    def _execute_move(self, move: Move):
        """Exécuter un mouvement."""
        player_hand = self.hands[move.player_id]
        
        if move.action == 'play':
            card = move.cards[0]
            # Retirer la carte de la main
            if card in player_hand:
                player_hand.remove(card)
                self.discard_pile.append(card)
                
                # Gérer les cartes spéciales
                if card.is_special_card() and move.target_suit:
                    self.current_suit = move.target_suit
                else:
                    self.current_suit = card.suit
        
        elif move.action == 'draw':
            # Piocher une carte
            if self.deck.is_empty():
                self._reshuffle_deck()
            
            drawn_card = self.deck.deal_card()
            if drawn_card:
                player_hand.append(drawn_card)
    
    def _reshuffle_deck(self):
        """Remettre les cartes de la défausse dans le deck (sauf la dernière)."""
        if len(self.discard_pile) > 1:
            cards_to_reshuffle = self.discard_pile[:-1]
            self.deck.add_cards(cards_to_reshuffle)
            self.deck.shuffle()
            self.discard_pile = [self.discard_pile[-1]]
    
    def _check_win_condition(self):
        """Vérifier les conditions de victoire."""
        for player in self.players:
            if len(self.hands[player]) == 0:
                self.game_over = True
                self.winner = player
                break
    
    def get_possible_moves(self, player_id: str) -> List[Move]:
        """Obtenir les mouvements possibles."""
        moves = []
        player_hand = self.hands[player_id]
        top_card = self.get_top_card()
        
        # Toujours possible de piocher
        moves.append(Move(player_id, 'draw', []))
        
        if top_card:
            for card in player_hand:
                # Tester si la carte peut être jouée
                test_move = Move(player_id, 'play', [card])
                if self.is_valid_move(test_move):
                    # Si c'est un 8, ajouter les options de couleur
                    if card.is_special_card():
                        for suit in Suit:
                            moves.append(Move(player_id, 'play', [card], target_suit=suit))
                    else:
                        moves.append(test_move)
        
        return moves
    
    def to_dict(self) -> dict:
        """Convertir l'état du jeu en dictionnaire."""
        state = super().to_dict()
        state.update({
            'game_type': 'crazy_eights',
            'discard_pile': [card.to_dict() for card in self.discard_pile],
            'top_card': self.get_top_card().to_dict() if self.get_top_card() else None,
            'current_suit': self.current_suit.value if self.current_suit else None
        })
        return state


class RummyGame(CardGameBase):
    """Jeu de Rami simplifié."""
    
    def __init__(self, num_players: int = 2):
        self.discard_pile: List[Card] = []
        self.melds: Dict[str, List[List[Card]]] = {}  # Combinaisons posées
        super().__init__(num_players)
    
    def _setup_game(self):
        """Configuration du Rami."""
        # Distribuer 10 cartes à chaque joueur
        self.deal_initial_hands(10)
        
        # Initialiser les combinaisons
        for player in self.players:
            self.melds[player] = []
        
        # Retourner la première carte
        first_card = self.deck.deal_card()
        if first_card:
            self.discard_pile.append(first_card)
    
    def get_top_discard(self) -> Optional[Card]:
        """Obtenir la carte du dessus de la défausse."""
        return self.discard_pile[-1] if self.discard_pile else None
    
    def is_valid_set(self, cards: List[Card]) -> bool:
        """Vérifier si c'est un brelan/carré valide."""
        if len(cards) < 3:
            return False
        
        # Tous doivent avoir la même valeur
        rank = cards[0].rank
        return all(card.rank == rank for card in cards)
    
    def is_valid_run(self, cards: List[Card]) -> bool:
        """Vérifier si c'est une séquence valide."""
        if len(cards) < 3:
            return False
        
        # Tous doivent être de la même couleur
        suit = cards[0].suit
        if not all(card.suit == suit for card in cards):
            return False
        
        # Vérifier la séquence
        sorted_cards = sorted(cards, key=lambda c: c.get_value())
        for i in range(1, len(sorted_cards)):
            if sorted_cards[i].get_value() != sorted_cards[i-1].get_value() + 1:
                return False
        
        return True
    
    def is_valid_move(self, move: Move) -> bool:
        """Vérifier si un mouvement est valide."""
        if move.action == 'draw':
            return True
        
        if move.action == 'play' and len(move.cards) == 1:
            # Défausser une carte
            return move.cards[0] in self.hands[move.player_id]
        
        if move.action == 'declare':
            # Déclarer une combinaison
            if move.meld_type == 'set':
                return self.is_valid_set(move.cards)
            elif move.meld_type == 'run':
                return self.is_valid_run(move.cards)
        
        return False
    
    def _execute_move(self, move: Move):
        """Exécuter un mouvement."""
        player_hand = self.hands[move.player_id]
        
        if move.action == 'draw':
            # Piocher du deck ou de la défausse
            if self.deck.size() > 0:
                drawn_card = self.deck.deal_card()
                if drawn_card:
                    player_hand.append(drawn_card)
        
        elif move.action == 'play':
            # Défausser une carte
            card = move.cards[0]
            if card in player_hand:
                player_hand.remove(card)
                self.discard_pile.append(card)
        
        elif move.action == 'declare':
            # Poser une combinaison
            for card in move.cards:
                if card in player_hand:
                    player_hand.remove(card)
            self.melds[move.player_id].append(move.cards)
    
    def _check_win_condition(self):
        """Vérifier les conditions de victoire."""
        for player in self.players:
            if len(self.hands[player]) == 0:
                self.game_over = True
                self.winner = player
                break
    
    def calculate_hand_value(self, player_id: str) -> int:
        """Calculer la valeur d'une main (cartes restantes)."""
        hand = self.hands[player_id]
        return sum(card.get_rummy_value() for card in hand)
    
    def get_possible_moves(self, player_id: str) -> List[Move]:
        """Obtenir les mouvements possibles."""
        moves = []
        player_hand = self.hands[player_id]
        
        # Piocher
        moves.append(Move(player_id, 'draw', []))
        
        # Défausser chaque carte
        for card in player_hand:
            moves.append(Move(player_id, 'play', [card]))
        
        # Chercher des combinaisons possibles
        # (Implémentation simplifiée - dans une version complète,
        # il faudrait tester toutes les combinaisons possibles)
        
        return moves
    
    def to_dict(self) -> dict:
        """Convertir l'état du jeu en dictionnaire."""
        state = super().to_dict()
        
        melds_dict = {}
        for player, player_melds in self.melds.items():
            melds_dict[player] = []
            for meld in player_melds:
                melds_dict[player].append([card.to_dict() for card in meld])
        
        state.update({
            'game_type': 'rummy',
            'discard_pile': [card.to_dict() for card in self.discard_pile],
            'top_discard': self.get_top_discard().to_dict() if self.get_top_discard() else None,
            'melds': melds_dict,
            'hand_values': {player: self.calculate_hand_value(player) for player in self.players}
        })
        return state


class WarGame(CardGameBase):
    """Jeu de Bataille."""
    
    def __init__(self, num_players: int = 2):
        self.war_piles: Dict[str, List[Card]] = {}
        self.battle_cards: List[Card] = []
        super().__init__(num_players)
    
    def _setup_game(self):
        """Configuration de la Bataille."""
        # Distribuer toutes les cartes
        cards_per_player = 52 // self.num_players
        
        for player in self.players:
            self.hands[player] = self.deck.deal_hand(cards_per_player)
            self.war_piles[player] = []
    
    def is_valid_move(self, move: Move) -> bool:
        """Vérifier si un mouvement est valide."""
        if move.action == 'play' and len(move.cards) == 1:
            return move.cards[0] in self.hands[move.player_id]
        return False
    
    def _execute_move(self, move: Move):
        """Exécuter un mouvement."""
        if move.action == 'play':
            card = move.cards[0]
            player_hand = self.hands[move.player_id]
            
            if card in player_hand:
                player_hand.remove(card)
                self.battle_cards.append(card)
        
        # Vérifier si tous les joueurs ont joué
        if len(self.battle_cards) == self.num_players:
            self._resolve_battle()
    
    def _resolve_battle(self):
        """Résoudre une bataille."""
        if not self.battle_cards:
            return
        
        # Trouver la carte la plus forte
        max_value = max(card.get_value() for card in self.battle_cards)
        winners = []
        
        for i, card in enumerate(self.battle_cards):
            if card.get_value() == max_value:
                winners.append(self.players[i])
        
        if len(winners) == 1:
            # Un seul gagnant
            winner = winners[0]
            self.war_piles[winner].extend(self.battle_cards)
        else:
            # Égalité - bataille !
            # Dans cette implémentation simplifiée, on partage les cartes
            cards_per_winner = len(self.battle_cards) // len(winners)
            for i, winner in enumerate(winners):
                start_idx = i * cards_per_winner
                end_idx = start_idx + cards_per_winner
                self.war_piles[winner].extend(self.battle_cards[start_idx:end_idx])
        
        self.battle_cards = []
    
    def _check_win_condition(self):
        """Vérifier les conditions de victoire."""
        players_with_cards = [p for p in self.players if len(self.hands[p]) > 0]
        
        if len(players_with_cards) <= 1:
            if players_with_cards:
                self.winner = players_with_cards[0]
            else:
                # Compter les cartes gagnées
                max_cards = max(len(pile) for pile in self.war_piles.values())
                for player, pile in self.war_piles.items():
                    if len(pile) == max_cards:
                        self.winner = player
                        break
            
            self.game_over = True
    
    def get_possible_moves(self, player_id: str) -> List[Move]:
        """Obtenir les mouvements possibles."""
        moves = []
        player_hand = self.hands[player_id]
        
        if player_hand:
            # En bataille, on joue la première carte
            moves.append(Move(player_id, 'play', [player_hand[0]]))
        
        return moves
    
    def to_dict(self) -> dict:
        """Convertir l'état du jeu en dictionnaire."""
        state = super().to_dict()
        
        war_piles_dict = {}
        for player, pile in self.war_piles.items():
            war_piles_dict[player] = len(pile)  # On ne montre que le nombre
        
        state.update({
            'game_type': 'war',
            'war_piles': war_piles_dict,
            'battle_cards': [card.to_dict() for card in self.battle_cards],
            'cards_in_play': len(self.battle_cards)
        })
        return state


class CardGameEngine:
    """Moteur de jeu de cartes pour RUMO RUSH."""
    
    def __init__(self, game_type: GameType, num_players: int = 2):
        self.game_type = game_type
        
        if game_type == GameType.CRAZY_EIGHTS:
            self.game = CrazyEightsGame(num_players)
        elif game_type == GameType.RUMMY:
            self.game = RummyGame(num_players)
        elif game_type == GameType.WAR:
            self.game = WarGame(num_players)
        else:
            raise ValueError(f"Type de jeu non supporté: {game_type}")
    
    def get_game_state(self) -> dict:
        """Obtenir l'état complet du jeu."""
        state = self.game.to_dict()
        
        # Ajouter des informations de jeu
        current_player = self.game.get_current_player()
        
        state.update({
            'status': self._get_game_status(),
            'current_player': current_player,
            'legal_moves': self._get_legal_moves_for_current_player(),
            'game_result': self._get_game_result()
        })
        
        return state
    
    def make_move_from_dict(self, move_data: dict) -> tuple[bool, str]:
        """Effectuer un mouvement depuis un dictionnaire."""
        try:
            action = move_data.get('action')
            cards_data = move_data.get('cards', [])
            target_suit = move_data.get('target_suit')
            meld_type = move_data.get('meld_type')
            
            if not action:
                return False, "Action manquante"
            
            # Convertir les cartes
            cards = []
            for card_data in cards_data:
                cards.append(Card.from_dict(card_data))
            
            # Convertir la couleur cible si nécessaire
            target_suit_enum = None
            if target_suit:
                target_suit_enum = Suit(target_suit)
            
            # Créer le mouvement
            current_player = self.game.get_current_player()
            move = Move(
                player_id=current_player,
                action=action,
                cards=cards,
                target_suit=target_suit_enum,
                meld_type=meld_type
            )
            
            # Effectuer le mouvement
            if self.game.make_move(move):
                return True, f"Mouvement effectué: {move}"
            else:
                return False, "Mouvement illégal"
                
        except Exception as e:
            return False, f"Erreur: {str(e)}"
    
    def is_game_over(self) -> bool:
        """Vérifier si le jeu est terminé."""
        return self.game.game_over
    
    def get_winner(self) -> Optional[str]:
        """Obtenir le gagnant si le jeu est terminé."""
        return self.game.winner
    
    def _get_game_status(self) -> str:
        """Obtenir le statut du jeu."""
        if self.game.game_over:
            return f"finished_{self.game.winner}" if self.game.winner else "finished_draw"
        else:
            return "playing"
    
    def _get_legal_moves_for_current_player(self) -> List[dict]:
        """Obtenir tous les mouvements légaux pour le joueur actuel."""
        current_player = self.game.get_current_player()
        moves = self.game.get_possible_moves(current_player)
        
        moves_list = []
        for move in moves:
            move_dict = {
                'action': move.action,
                'cards': [card.to_dict() for card in move.cards]
            }
            
            if move.target_suit:
                move_dict['target_suit'] = move.target_suit.value
            
            if move.meld_type:
                move_dict['meld_type'] = move.meld_type
            
            moves_list.append(move_dict)
        
        return moves_list
    
    def _get_game_result(self) -> Optional[dict]:
        """Obtenir le résultat du jeu."""
        if not self.game.game_over:
            return None
        
        if self.game.winner:
            return {
                'result': 'win',
                'winner': self.game.winner,
                'reason': 'cards_finished'
            }
        
        return {
            'result': 'draw',
            'reason': 'stalemate'
        }
    
    def reset_game(self):
        """Réinitialiser le jeu."""
        num_players = self.game.num_players
        self.__init__(self.game_type, num_players)
    
    def validate_move_format(self, move_data: dict) -> tuple[bool, str]:
        """Valider le format des données de mouvement."""
        if 'action' not in move_data:
            return False, "Champ 'action' manquant"
        
        action = move_data['action']
        valid_actions = ['play', 'draw', 'declare', 'pass']
        
        if action not in valid_actions:
            return False, f"Action invalide. Doit être l'une de: {valid_actions}"
        
        # Valider les cartes si nécessaire
        if action in ['play', 'declare']:
            cards = move_data.get('cards', [])
            if not cards:
                return False, f"Cartes requises pour l'action '{action}'"
            
            for card_data in cards:
                if not isinstance(card_data, dict) or 'suit' not in card_data or 'rank' not in card_data:
                    return False, "Format de carte invalide"
        
        return True, "Format valide"


# Fonctions utilitaires pour l'intégration avec Django

def create_cards_game(game_type: str, num_players: int = 2) -> dict:
    """Créer une nouvelle partie de cartes."""
    try:
        game_type_enum = GameType(game_type)
        engine = CardGameEngine(game_type_enum, num_players)
        return engine.get_game_state()
    except ValueError:
        raise ValueError(f"Type de jeu non supporté: {game_type}")

def make_cards_move(game_data: dict, move_data: dict) -> tuple[dict, bool, str]:
    """Effectuer un mouvement dans une partie de cartes."""
    try:
        # Reconstruire l'état du jeu
        game_type = GameType(game_data['game_type'])
        num_players = len(game_data['players'])
        engine = CardGameEngine(game_type, num_players)
        
        # Restaurer l'état (implémentation simplifiée)
        # Dans une version complète, il faudrait restaurer complètement l'état
        
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

def check_cards_win_condition(game_data: dict) -> tuple[bool, Optional[str], str]:
    """Vérifier les conditions de victoire aux cartes."""
    try:
        game_type = GameType(game_data['game_type'])
        num_players = len(game_data['players'])
        engine = CardGameEngine(game_type, num_players)
        
        # Restaurer l'état du jeu (simplifié)
        engine.game.game_over = game_data.get('game_over', False)
        engine.game.winner = game_data.get('winner')
        
        if engine.is_game_over():
            winner = engine.get_winner()
            result = engine._get_game_result()
            
            if result:
                return True, winner, result['reason']
        
        return False, None, "Jeu en cours"
        
    except Exception as e:
        return False, None, f"Erreur: {str(e)}"

def get_cards_legal_moves(game_data: dict) -> list:
    """Obtenir les mouvements légaux pour le joueur actuel."""
    try:
        game_type = GameType(game_data['game_type'])
        num_players = len(game_data['players'])
        engine = CardGameEngine(game_type, num_players)
        
        # Restaurer l'état (simplifié)
        current_player_index = game_data.get('current_player_index', 0)
        engine.game.current_player_index = current_player_index
        
        return engine._get_legal_moves_for_current_player()
    except Exception:
        return []

def get_player_hand(game_data: dict, player_id: str) -> list:
    """Obtenir la main d'un joueur."""
    try:
        hands = game_data.get('hands', {})
        return hands.get(player_id, [])
    except Exception:
        return []

def calculate_game_score(game_data: dict) -> dict:
    """Calculer les scores selon le type de jeu."""
    try:
        scores = {}
        game_type = game_data.get('game_type')
        
        if game_type == 'rummy':
            # Pour le Rami, calculer les valeurs des mains
            hand_values = game_data.get('hand_values', {})
            for player, value in hand_values.items():
                scores[player] = -value  # Moins de points = mieux
        
        elif game_type == 'war':
            # Pour la Bataille, compter les cartes gagnées
            war_piles = game_data.get('war_piles', {})
            for player, pile_size in war_piles.items():
                scores[player] = pile_size
        
        elif game_type == 'crazy_eights':
            # Pour le Huit américain, compter les cartes restantes
            hands = game_data.get('hands', {})
            for player, hand in hands.items():
                scores[player] = -len(hand)  # Moins de cartes = mieux
        
        return scores
        
    except Exception:
        return {}


# Classes utilitaires supplémentaires

class CardGameAnalyzer:
    """Analyseur pour les statistiques de jeu."""
    
    def __init__(self, game_data: dict):
        self.game_data = game_data
        self.game_type = game_data.get('game_type')
    
    def analyze_game_performance(self, player_id: str) -> dict:
        """Analyser la performance d'un joueur."""
        analysis = {
            'cards_played': 0,
            'moves_made': 0,
            'cards_remaining': 0,
            'efficiency_score': 0.0
        }
        
        try:
            # Compter les cartes restantes
            hands = self.game_data.get('hands', {})
            player_hand = hands.get(player_id, [])
            analysis['cards_remaining'] = len(player_hand)
            
            # Analyser l'historique des mouvements
            move_history = self.game_data.get('move_history', [])
            player_moves = [move for move in move_history if player_id in str(move)]
            analysis['moves_made'] = len(player_moves)
            
            # Calculer un score d'efficacité (simplifié)
            if analysis['moves_made'] > 0:
                analysis['efficiency_score'] = max(0, 1 - (analysis['cards_remaining'] / 10))
            
            return analysis
            
        except Exception:
            return analysis
    
    def get_game_statistics(self) -> dict:
        """Obtenir les statistiques globales du jeu."""
        stats = {
            'total_moves': len(self.game_data.get('move_history', [])),
            'game_duration_moves': len(self.game_data.get('move_history', [])),
            'cards_in_play': 0,
            'game_complexity': 'simple'
        }
        
        try:
            # Calculer les cartes en jeu
            hands = self.game_data.get('hands', {})
            total_cards = sum(len(hand) for hand in hands.values())
            stats['cards_in_play'] = total_cards
            
            # Déterminer la complexité du jeu
            if self.game_type == 'rummy':
                stats['game_complexity'] = 'complex'
            elif self.game_type == 'crazy_eights':
                stats['game_complexity'] = 'medium'
            else:
                stats['game_complexity'] = 'simple'
            
            return stats
            
        except Exception:
            return stats


class CardGameValidator:
    """Validateur pour les jeux de cartes."""
    
    @staticmethod
    def validate_game_state(game_data: dict) -> tuple[bool, str]:
        """Valider l'état d'un jeu."""
        required_fields = ['game_type', 'players', 'hands', 'current_player_index']
        
        for field in required_fields:
            if field not in game_data:
                return False, f"Champ manquant: {field}"
        
        # Valider le type de jeu
        try:
            GameType(game_data['game_type'])
        except ValueError:
            return False, f"Type de jeu invalide: {game_data['game_type']}"
        
        # Valider les joueurs
        players = game_data['players']
        if not isinstance(players, list) or len(players) < 2:
            return False, "Au moins 2 joueurs requis"
        
        # Valider l'index du joueur actuel
        current_index = game_data['current_player_index']
        if not isinstance(current_index, int) or current_index >= len(players):
            return False, "Index de joueur actuel invalide"
        
        # Valider les mains
        hands = game_data['hands']
        if not isinstance(hands, dict):
            return False, "Format des mains invalide"
        
        for player in players:
            if player not in hands:
                return False, f"Main manquante pour le joueur: {player}"
        
        return True, "État valide"
    
    @staticmethod
    def validate_card_data(card_data: dict) -> tuple[bool, str]:
        """Valider les données d'une carte."""
        if not isinstance(card_data, dict):
            return False, "Les données de carte doivent être un dictionnaire"
        
        if 'suit' not in card_data or 'rank' not in card_data:
            return False, "Champs 'suit' et 'rank' requis"
        
        try:
            Suit(card_data['suit'])
            Rank(card_data['rank'])
        except ValueError as e:
            return False, f"Valeur de carte invalide: {e}"
        
        return True, "Carte valide"
    
    @staticmethod
    def validate_hand_size(game_type: str, hand_size: int) -> tuple[bool, str]:
        """Valider la taille d'une main selon le type de jeu."""
        max_sizes = {
            'crazy_eights': 7,
            'rummy': 10,
            'war': 26  # Pour 2 joueurs
        }
        
        max_size = max_sizes.get(game_type, 13)
        
        if hand_size > max_size:
            return False, f"Taille de main trop importante pour {game_type}: {hand_size} > {max_size}"
        
        return True, "Taille de main valide"


# Utilitaires de configuration pour différents types de jeux

GAME_CONFIGURATIONS = {
    'crazy_eights': {
        'initial_hand_size': 7,
        'deck_size': 52,
        'special_cards': ['8'],
        'win_condition': 'empty_hand',
        'supports_suits': True
    },
    'rummy': {
        'initial_hand_size': 10,
        'deck_size': 52,
        'special_cards': [],
        'win_condition': 'empty_hand_or_declare',
        'supports_melds': True
    },
    'war': {
        'initial_hand_size': 26,  # Pour 2 joueurs
        'deck_size': 52,
        'special_cards': [],
        'win_condition': 'most_cards',
        'automatic_play': True
    }
}

def get_game_configuration(game_type: str) -> dict:
    """Obtenir la configuration d'un type de jeu."""
    return GAME_CONFIGURATIONS.get(game_type, {})

def is_game_type_supported(game_type: str) -> bool:
    """Vérifier si un type de jeu est supporté."""
    try:
        GameType(game_type)
        return True
    except ValueError:
        return False

def get_supported_game_types() -> List[str]:
    """Obtenir la liste des types de jeux supportés."""
    return [game_type.value for game_type in GameType]

def estimate_game_duration(game_type: str, num_players: int) -> dict:
    """Estimer la durée d'une partie."""
    base_durations = {
        'crazy_eights': 10,  # minutes
        'rummy': 20,
        'war': 5
    }
    
    base_duration = base_durations.get(game_type, 15)
    
    # Ajuster selon le nombre de joueurs
    multiplier = 1 + (num_players - 2) * 0.3
    estimated_duration = int(base_duration * multiplier)
    
    return {
        'estimated_minutes': estimated_duration,
        'estimated_moves': estimated_duration * 2,  # Approximation
        'complexity': get_game_configuration(game_type).get('complexity', 'medium')
    }
