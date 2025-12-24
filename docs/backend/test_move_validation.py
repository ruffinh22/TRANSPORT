#!/usr/bin/env python3
"""
Test de validation du mouvement compétitif.
"""

import sys
import os
import django

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rumo_rush.settings.testing')
django.setup()

from apps.games.game_logic.checkers_competitive import (
    create_competitive_checkers_game,
    CheckersBoard,
    Position
)

def test_move_validation():
    """Tester la validation d'un mouvement."""
    
    print("🎯 Test de validation de mouvement compétitif\n")
    
    # Créer une partie
    game_data = create_competitive_checkers_game()
    board = CheckersBoard.from_dict(game_data)
    
    print(f"Joueur actuel: {board.current_player.value}")
    print(f"Timer: {game_data['timer']['red_time_remaining']}s RED, {game_data['timer']['black_time_remaining']}s BLACK\n")
    
    # Tester un mouvement valide pour RED (position 6,1 -> 5,0)
    from_pos = Position(6, 1)
    to_pos = Position(5, 0)
    
    piece = board.get_piece(from_pos)
    print(f"Pièce à (6,1): {piece.color.value if piece else 'None'} {piece.piece_type.value if piece else ''}")
    
    possible_moves = board.get_possible_moves(from_pos)
    print(f"Mouvements possibles depuis (6,1): {[(m.to_pos.row, m.to_pos.col) for m in possible_moves]}")
    
    # Vérifier si (5,0) est valide
    is_valid = any(m.to_pos.row == 5 and m.to_pos.col == 0 for m in possible_moves)
    print(f"\nMouvement (6,1) -> (5,0) valide: {'✅ OUI' if is_valid else '❌ NON'}")
    
    if is_valid:
        print("\n✅ TEST RÉUSSI: La validation fonctionne correctement!")
        return 0
    else:
        print("\n❌ TEST ÉCHOUÉ: Le mouvement devrait être valide")
        return 1

if __name__ == '__main__':
    sys.exit(test_move_validation())
