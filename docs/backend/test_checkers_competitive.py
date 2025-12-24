#!/usr/bin/env python3
"""
Test script pour le jeu de dames compétitif 10x10
"""

from apps.games.game_logic.checkers_competitive import (
    create_competitive_checkers_game, 
    get_competitive_legal_moves,
    make_competitive_move
)

def test_game_creation():
    """Test de création de partie"""
    print('🎮 Création d\'une partie de dames compétitive 10x10...')
    game = create_competitive_checkers_game()
    
    print(f'✅ Plateau: {game["size"]}x{game["size"]}')
    print(f'✅ Joueur actuel: {game["current_player"]}')
    print(f'✅ Score rouge: {game["red_score"]["points"]} points')
    print(f'✅ Score noir: {game["black_score"]["points"]} points')
    print(f'✅ Timer global: {game["timer"]["global_time_limit"]}s')
    print(f'✅ Timer par coup: {game["timer"]["move_time_limit"]}s')
    
    # Vérifier les pièces initiales
    red_pieces = sum(1 for row in game['board'] for cell in row if cell and cell['color'] == 'red')
    black_pieces = sum(1 for row in game['board'] for cell in row if cell and cell['color'] == 'black')
    print(f'✅ Pièces rouges: {red_pieces}/20')
    print(f'✅ Pièces noires: {black_pieces}/20')
    
    return game

def test_legal_moves(game):
    """Test des mouvements légaux"""
    print('\n🎯 Test des mouvements légaux:')
    
    # Trouver un pion rouge sur le plateau
    for row in range(10):
        for col in range(10):
            if game['board'][row][col] and game['board'][row][col]['color'] == 'red':
                moves = get_competitive_legal_moves(game, row, col)
                if moves:
                    print(f'   Pion rouge en ({row}, {col}): {len(moves)} coup(s) possible(s)')
                    for move in moves[:3]:  # Afficher max 3 coups
                        print(f'      → ({move["to"]["row"]}, {move["to"]["col"]}) - {move["points"]} point(s)')
                    return
    
    print('   Aucun coup trouvé')

def test_simple_move(game):
    """Test d'un mouvement simple"""
    print('\n🎲 Test d\'un mouvement simple:')
    
    # Trouver un coup légal
    for row in range(10):
        for col in range(10):
            if game['board'][row][col] and game['board'][row][col]['color'] == 'red':
                moves = get_competitive_legal_moves(game, row, col)
                if moves:
                    move = moves[0]
                    print(f'   Déplacement de ({row}, {col}) vers ({move["to"]["row"]}, {move["to"]["col"]})')
                    
                    result = make_competitive_move(game, row, col, move["to"]["row"], move["to"]["col"])
                    
                    if result['success']:
                        print(f'   ✅ Mouvement réussi!')
                        print(f'   Points gagnés: {result["points_gained"]}')
                        print(f'   Score rouge: {result["game_state"]["red_score"]["points"]}')
                        print(f'   Joueur suivant: {result["game_state"]["current_player"]}')
                    else:
                        print(f'   ❌ Erreur: {result["error"]}')
                    
                    return result
    
    print('   Aucun mouvement possible')
    return None

if __name__ == '__main__':
    print('=' * 60)
    print('🏁 Test du jeu de Dames Compétitif 10x10')
    print('=' * 60)
    
    # Test 1: Création de partie
    game = test_game_creation()
    
    # Test 2: Mouvements légaux
    test_legal_moves(game)
    
    # Test 3: Faire un mouvement
    test_simple_move(game)
    
    print('\n' + '=' * 60)
    print('✨ Tests terminés avec succès!')
    print('=' * 60)
