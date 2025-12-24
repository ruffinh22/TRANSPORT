#!/usr/bin/env python
"""
Script de diagnostic pour vérifier l'état d'un jeu d'échecs et détecter pat/mat.
"""

import os
import sys
import django
import json

# Configuration Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rumo_rush.settings')
django.setup()

from apps.games.models import Game
from apps.games.game_logic.chess_competitive import (
    is_checkmate,
    is_stalemate,
    has_legal_moves,
    is_in_check,
    find_king,
    get_possible_moves,
    is_move_legal,
    check_competitive_chess_game_over
)


def diagnose_chess_game(room_code_or_id):
    """Diagnostiquer l'état d'un jeu d'échecs."""
    
    print(f"\n{'='*80}")
    print(f"🔍 DIAGNOSTIC JEU D'ÉCHECS - {room_code_or_id}")
    print(f"{'='*80}\n")
    
    # Trouver le jeu
    try:
        if len(room_code_or_id) == 8:  # room_code
            game = Game.objects.get(room_code=room_code_or_id)
        else:  # UUID
            game = Game.objects.get(id=room_code_or_id)
    except Game.DoesNotExist:
        print(f"❌ Jeu non trouvé: {room_code_or_id}")
        return
    
    print(f"✅ Jeu trouvé: {game.room_code} (ID: {game.id})")
    print(f"   Status: {game.status}")
    print(f"   Player1 (WHITE): {game.player1.username}")
    print(f"   Player2 (BLACK): {game.player2.username}")
    
    if not game.game_data:
        print(f"❌ Pas de game_data disponible")
        return
    
    board = game.game_data.get('board', [])
    current_player = game.game_data.get('current_player', 'white')
    
    print(f"\n📊 ÉTAT DE LA PARTIE")
    print(f"   Joueur actuel: {current_player.upper()}")
    print(f"   Current player (model): {game.current_player.username if game.current_player else 'None'}")
    
    # Afficher le plateau
    print(f"\n♟️  PLATEAU D'ÉCHECS (Unicode):")
    print(f"   ┌─────────────────┐")
    for i, row in enumerate(board):
        row_str = ' '.join([cell if cell and cell != '.' else '·' for cell in row])
        print(f" {8-i} │ {row_str} │")
    print(f"   └─────────────────┘")
    print(f"     a b c d e f g h")
    
    # Afficher le plateau brut
    print(f"\n🔍 PLATEAU BRUT (structure interne):")
    for i, row in enumerate(board):
        print(f"   Row {i}: {row}")
    
    # Trouver les rois
    white_king_pos = find_king(board, 'white')
    black_king_pos = find_king(board, 'black')
    
    print(f"\n👑 POSITION DES ROIS:")
    if white_king_pos:
        print(f"   Roi blanc: {chr(97 + white_king_pos[1])}{8 - white_king_pos[0]}")
    else:
        print(f"   ❌ Roi blanc non trouvé!")
    
    if black_king_pos:
        print(f"   Roi noir: {chr(97 + black_king_pos[1])}{8 - black_king_pos[0]}")
    else:
        print(f"   ❌ Roi noir non trouvé!")
    
    # Vérifier les échecs
    white_in_check = is_in_check(board, 'white')
    black_in_check = is_in_check(board, 'black')
    
    print(f"\n⚠️  ÉCHECS:")
    print(f"   Blanc en échec: {'✅ OUI' if white_in_check else '❌ NON'}")
    print(f"   Noir en échec: {'✅ OUI' if black_in_check else '❌ NON'}")
    
    # Analyser les pièces blanches
    print(f"\n♙ PIÈCES BLANCHES ET MOUVEMENTS POSSIBLES:")
    white_pieces = []
    total_white_moves = 0
    total_white_legal_moves = 0
    
    for row in range(8):
        for col in range(8):
            piece = board[row][col]
            if piece and isinstance(piece, dict) and piece.get('color') == 'white':
                pos_notation = f"{chr(97 + col)}{8 - row}"
                piece_type = piece.get('type', '?')
                white_pieces.append((pos_notation, piece_type))
                
                # Mouvements possibles
                moves = get_possible_moves(board, row, col)
                legal_moves = []
                for move_row, move_col in moves:
                    if is_move_legal(board, row, col, move_row, move_col, 'white'):
                        legal_moves.append(f"{chr(97 + move_col)}{8 - move_row}")
                
                total_white_moves += len(moves)
                total_white_legal_moves += len(legal_moves)
                
                print(f"   {piece_type} en {pos_notation}: {len(moves)} coups possibles, {len(legal_moves)} légaux")
                if legal_moves:
                    print(f"      → Coups légaux: {', '.join(legal_moves)}")
    
    print(f"\n   TOTAL: {len(white_pieces)} pièces, {total_white_moves} coups possibles, {total_white_legal_moves} légaux")
    
    # Analyser les pièces noires
    print(f"\n♟ PIÈCES NOIRES ET MOUVEMENTS POSSIBLES:")
    black_pieces = []
    total_black_moves = 0
    total_black_legal_moves = 0
    
    for row in range(8):
        for col in range(8):
            piece = board[row][col]
            if piece and isinstance(piece, dict) and piece.get('color') == 'black':
                pos_notation = f"{chr(97 + col)}{8 - row}"
                piece_type = piece.get('type', '?')
                black_pieces.append((pos_notation, piece_type))
                
                # Mouvements possibles
                moves = get_possible_moves(board, row, col)
                legal_moves = []
                for move_row, move_col in moves:
                    if is_move_legal(board, row, col, move_row, move_col, 'black'):
                        legal_moves.append(f"{chr(97 + move_col)}{8 - move_row}")
                
                total_black_moves += len(moves)
                total_black_legal_moves += len(legal_moves)
                
                print(f"   {piece_type} en {pos_notation}: {len(moves)} coups possibles, {len(legal_moves)} légaux")
                if legal_moves:
                    print(f"      → Coups légaux: {', '.join(legal_moves)}")
    
    print(f"\n   TOTAL: {len(black_pieces)} pièces, {total_black_moves} coups possibles, {total_black_legal_moves} légaux")
    
    # Diagnostics spécifiques
    white_has_moves = has_legal_moves(board, 'white')
    black_has_moves = has_legal_moves(board, 'black')
    
    print(f"\n🎯 DIAGNOSTICS:")
    print(f"   Blanc a des coups légaux: {'✅ OUI' if white_has_moves else '❌ NON'}")
    print(f"   Noir a des coups légaux: {'✅ OUI' if black_has_moves else '❌ NON'}")
    
    # Vérifier mat/pat
    white_checkmate = is_checkmate(board, 'white')
    white_stalemate = is_stalemate(board, 'white')
    black_checkmate = is_checkmate(board, 'black')
    black_stalemate = is_stalemate(board, 'black')
    
    print(f"\n🏁 CONDITIONS DE FIN:")
    print(f"   Blanc échec et mat: {'✅ OUI' if white_checkmate else '❌ NON'}")
    print(f"   Blanc pat (stalemate): {'✅ OUI' if white_stalemate else '❌ NON'}")
    print(f"   Noir échec et mat: {'✅ OUI' if black_checkmate else '❌ NON'}")
    print(f"   Noir pat (stalemate): {'✅ OUI' if black_stalemate else '❌ NON'}")
    
    # Vérifier avec la fonction complète
    is_over, winner, details = check_competitive_chess_game_over(game.game_data)
    
    print(f"\n🎮 RÉSULTAT DE check_competitive_chess_game_over:")
    print(f"   Partie terminée: {'✅ OUI' if is_over else '❌ NON'}")
    print(f"   Gagnant: {winner if winner else 'Aucun'}")
    print(f"   Détails: {json.dumps(details, indent=2)}")
    
    # Scores
    white_score = game.game_data.get('white_score', {})
    black_score = game.game_data.get('black_score', {})
    
    print(f"\n📊 SCORES:")
    print(f"   Blanc: {white_score.get('points', 0)} points ({white_score.get('pieces_captured', 0)} pièces capturées)")
    print(f"   Noir: {black_score.get('points', 0)} points ({black_score.get('pieces_captured', 0)} pièces capturées)")
    
    # Timer
    timer = game.game_data.get('timer', {})
    print(f"\n⏱️  TIMER:")
    print(f"   Temps blanc restant: {timer.get('white_time_remaining', 0):.1f}s")
    print(f"   Temps noir restant: {timer.get('black_time_remaining', 0):.1f}s")
    print(f"   Temps coup restant: {timer.get('move_time_remaining', 0):.1f}s")
    
    # Conclusion
    print(f"\n{'='*80}")
    print(f"📝 CONCLUSION:")
    print(f"{'='*80}")
    
    if current_player == 'white':
        if white_checkmate:
            print(f"🏆 Les NOIRS ont gagné par ÉCHEC ET MAT!")
        elif white_stalemate:
            print(f"🤝 PAT! Les blancs n'ont aucun coup légal mais ne sont pas en échec.")
            print(f"   → Selon les règles compétitives, on compare les points:")
            if white_score.get('points', 0) > black_score.get('points', 0):
                print(f"   → BLANC GAGNE ({white_score.get('points', 0)} vs {black_score.get('points', 0)} points)")
            elif black_score.get('points', 0) > white_score.get('points', 0):
                print(f"   → NOIR GAGNE ({black_score.get('points', 0)} vs {white_score.get('points', 0)} points)")
            else:
                print(f"   → MATCH NUL (égalité de points)")
        elif not white_has_moves:
            print(f"⚠️  ANOMALIE: Les blancs n'ont aucun coup légal mais ce n'est ni mat ni pat!")
        else:
            print(f"✅ La partie peut continuer, c'est au tour des blancs.")
    else:
        if black_checkmate:
            print(f"🏆 Les BLANCS ont gagné par ÉCHEC ET MAT!")
        elif black_stalemate:
            print(f"🤝 PAT! Les noirs n'ont aucun coup légal mais ne sont pas en échec.")
            print(f"   → Selon les règles compétitives, on compare les points:")
            if white_score.get('points', 0) > black_score.get('points', 0):
                print(f"   → BLANC GAGNE ({white_score.get('points', 0)} vs {black_score.get('points', 0)} points)")
            elif black_score.get('points', 0) > white_score.get('points', 0):
                print(f"   → NOIR GAGNE ({black_score.get('points', 0)} vs {white_score.get('points', 0)} points)")
            else:
                print(f"   → MATCH NUL (égalité de points)")
        elif not black_has_moves:
            print(f"⚠️  ANOMALIE: Les noirs n'ont aucun coup légal mais ce n'est ni mat ni pat!")
        else:
            print(f"✅ La partie peut continuer, c'est au tour des noirs.")
    
    print(f"\n{'='*80}\n")


if __name__ == '__main__':
    if len(sys.argv) < 2:
        # Trouver la dernière partie d'échecs (même terminée)
        print("🔍 Recherche des parties d'échecs récentes...")
        games = Game.objects.filter(
            game_type__name='chess'
        ).order_by('-created_at')[:10]
        
        if games.exists():
            print(f"\n📋 {games.count()} partie(s) d'échecs trouvée(s):")
            print("=" * 80)
            for i, g in enumerate(games, 1):
                last_move = g.last_move_at.strftime('%Y-%m-%d %H:%M') if g.last_move_at else 'N/A'
                print(f"{i}. {g.room_code} | Status: {g.status} | Dernier coup: {last_move}")
                if g.game_data:
                    current = g.game_data.get('current_player', '?')
                    is_over = g.game_data.get('is_game_over', False)
                    winner = g.game_data.get('winner', 'N/A')
                    print(f"   Tour: {current} | Game Over: {is_over} | Winner: {winner}")
            print("=" * 80)
            
            # Analyser la plus récente
            game = games.first()
            print(f"\n🔍 Analyse de la partie la plus récente: {game.room_code}\n")
            diagnose_chess_game(game.room_code)
        else:
            print("❌ Aucune partie d'échecs trouvée.")
            print("\nUsage: python diagnose_chess_stalemate.py <room_code|game_id>")
    else:
        room_code_or_id = sys.argv[1]
        diagnose_chess_game(room_code_or_id)
