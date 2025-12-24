#!/usr/bin/env python
"""Test de la promotion des pions noirs en dames noires."""

import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'backend.settings')
django.setup()

from apps.games.game_logic.checkers_competitive import (
    CheckersBoard, Position, Color, PieceType, CheckersPiece,
    convert_board_to_unicode
)

def test_black_promotion():
    """Tester la promotion d'un pion noir."""
    print("\n" + "="*60)
    print("🧪 TEST: Promotion d'un pion noir en dame noire")
    print("="*60)
    
    # Créer un plateau vide
    board = CheckersBoard()
    board.board = [[None for _ in range(10)] for _ in range(10)]
    
    # ✅ Les pions NOIRS commencent en haut (lignes 0-3) et descendent vers la ligne 9
    # ✅ Promotion noire = atteindre la ligne 9 (dernière ligne)
    # ✅ Les pièces doivent être sur des cases noires (row+col = impair)
    # Placer un pion NOIR à la ligne 8, colonne 1 (case noire, prêt à être promu)
    black_pawn = CheckersPiece(PieceType.MAN, Color.BLACK)
    board.set_piece(Position(8, 1), black_pawn)
    
    print(f"\n📍 Position initiale:")
    print(f"   Pion noir en (8,1): {black_pawn.color.value} {black_pawn.piece_type.value}")
    
    # Vérifier que la pièce existe
    piece_at_start = board.get_piece(Position(8, 1))
    print(f"   Vérification: {piece_at_start.color.value} {piece_at_start.piece_type.value}")
    
    # Créer un mouvement de promotion manuel
    board.current_player = Color.BLACK
    
    # Déplacer le pion noir de (8,1) vers (9,0) ou (9,2) - promotion garantie
    from_pos = Position(8, 1)
    to_pos = Position(9, 0)  # ou (9,2)
    
    # Trouver les mouvements possibles
    possible_moves = board.get_possible_moves(from_pos)
    print(f"\n🎯 Mouvements possibles depuis (8,1): {len(possible_moves)}")
    for move in possible_moves:
        print(f"   - Vers {move.to_pos}, promotion={move.is_promotion}")
    
    # Prendre le premier mouvement disponible (devrait être une promotion)
    if not possible_moves:
        print(f"❌ ERREUR: Aucun mouvement possible depuis (8,1)")
        return
    
    promotion_move = possible_moves[0]
    to_pos = promotion_move.to_pos
    
    if not promotion_move.is_promotion:
        print(f"⚠️ ATTENTION: Le mouvement n'est pas marqué comme promotion!")
        print(f"   Destination: ligne {to_pos.row} (devrait être 9 pour promotion noire)")
    
    print(f"\n🎬 Exécution du mouvement de promotion...")
    print(f"   De: {promotion_move.from_pos}")
    print(f"   Vers: {promotion_move.to_pos}")
    print(f"   Est promotion: {promotion_move.is_promotion}")
    
    # Exécuter le mouvement
    success = board.make_move(promotion_move)
    
    if not success:
        print(f"❌ ERREUR: Échec de l'exécution du mouvement")
        return
    
    print(f"✅ Mouvement exécuté avec succès!")
    
    # Vérifier la pièce à la position finale
    promoted_piece = board.get_piece(to_pos)
    
    print(f"\n🔍 Vérification de la pièce promue:")
    if promoted_piece:
        print(f"   Position: {to_pos}")
        print(f"   Type: {promoted_piece.piece_type.value} (attendu: 'king')")
        print(f"   Couleur: {promoted_piece.color.value} (attendu: 'black')")
        
        # Tester la conversion en dict
        game_data = board.to_dict()
        cell_data = game_data['board'][to_pos.row][to_pos.col]
        
        print(f"\n📊 Données brutes (to_dict):")
        print(f"   {cell_data}")
        
        # Tester la conversion en unicode
        unicode_board = convert_board_to_unicode(game_data)
        unicode_piece = unicode_board[to_pos.row][to_pos.col]
        
        print(f"\n🎨 Conversion Unicode:")
        print(f"   Caractère: {unicode_piece} (attendu: '♛' pour dame noire)")
        
        # Résultat
        if (promoted_piece.piece_type == PieceType.KING and 
            promoted_piece.color == Color.BLACK and 
            unicode_piece == '♛'):
            print(f"\n✅ ✅ ✅ TEST RÉUSSI! ✅ ✅ ✅")
            print(f"Le pion noir a été correctement promu en dame noire (♛)")
        else:
            print(f"\n❌ ❌ ❌ TEST ÉCHOUÉ! ❌ ❌ ❌")
            if promoted_piece.piece_type != PieceType.KING:
                print(f"   Problème: Type incorrect ({promoted_piece.piece_type.value})")
            if promoted_piece.color != Color.BLACK:
                print(f"   Problème: Couleur incorrecte ({promoted_piece.color.value})")
            if unicode_piece != '♛':
                print(f"   Problème: Unicode incorrect ({unicode_piece})")
    else:
        print(f"❌ ERREUR: Aucune pièce trouvée à la position {to_pos} après promotion!")
    
    print("\n" + "="*60 + "\n")

if __name__ == '__main__':
    test_black_promotion()
