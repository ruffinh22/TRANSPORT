#!/usr/bin/env python3
"""
Script de test pour vérifier les corrections Ludo:
1. Rejouer après un 6
2. Capture des pions en avant et en arrière
"""

import os
import django
import sys

# Setup Django
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rumo_rush.settings')
django.setup()

from apps.games.models import Game
from apps.accounts.models import User
from apps.games.game_logic.ludo_competitive import create_competitive_ludo_game
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_six_replay():
    """Test que le joueur peut rejouer après un 6."""
    print("\n" + "="*60)
    print("TEST 1: Rejouer après un 6")
    print("="*60)
    
    # Créer des joueurs de test
    user1, _ = User.objects.get_or_create(
        username='test_ludo_1',
        defaults={'email': 'test1@ludo.com', 'balance': 100}
    )
    user2, _ = User.objects.get_or_create(
        username='test_ludo_2',
        defaults={'email': 'test2@ludo.com', 'balance': 100}
    )
    
    # Créer une partie
    game = Game.objects.create(
        game_type='ludo',
        mode='competitive',
        player1=user1,
        player2=user2,
        status='playing',
        bet_amount=10,
        game_data=create_competitive_ludo_game()
    )
    
    # Configurer les couleurs des joueurs
    game.game_data['player_colors'] = {
        str(user1.id): 'red',
        str(user2.id): 'blue'
    }
    game.game_data['current_player'] = 'red'
    game.save()
    
    print(f"✅ Partie créée: {game.id}")
    print(f"   Joueur 1 (Rouge): {user1.username}")
    print(f"   Joueur 2 (Bleu): {user2.username}")
    
    # Simuler un lancer de dé = 6
    print("\n📍 TEST: Lancer un 6")
    game.game_data['current_dice_value'] = 6
    game.game_data['consecutive_sixes'] = 1
    game.save()
    
    # Trouver un pion à déplacer
    pieces = game.game_data.get('pieces', [])
    red_piece = None
    for piece in pieces:
        if piece['color'] == 'red' and piece['position'] == -1:
            red_piece = piece['id']
            break
    
    if red_piece:
        print(f"   Pion trouvé: {red_piece}")
        # Déplacer le pion
        success = game.process_ludo_piece_move(user1, red_piece, 6)
        
        if success:
            print(f"\n✅ Déplacement réussi!")
            print(f"   can_roll_dice: {game.game_data.get('can_roll_dice')}")
            print(f"   current_player: {game.game_data.get('current_player')}")
            print(f"   current_dice_value: {game.game_data.get('current_dice_value')}")
            
            # Vérifier que le joueur peut rejouer
            if game.game_data.get('can_roll_dice') and game.game_data.get('current_player') == 'red':
                print("\n✅ TEST RÉUSSI: Le joueur peut rejouer après un 6!")
            else:
                print("\n❌ TEST ÉCHOUÉ: Le joueur ne peut pas rejouer après un 6")
        else:
            print("❌ Échec du déplacement")
    
    # Nettoyer
    game.delete()
    print("\n🧹 Partie de test supprimée")


def test_capture():
    """Test de la capture de pions."""
    print("\n" + "="*60)
    print("TEST 2: Capture de pions")
    print("="*60)
    
    # Créer des joueurs de test
    user1, _ = User.objects.get_or_create(
        username='test_ludo_capture_1',
        defaults={'email': 'testc1@ludo.com', 'balance': 100}
    )
    user2, _ = User.objects.get_or_create(
        username='test_ludo_capture_2',
        defaults={'email': 'testc2@ludo.com', 'balance': 100}
    )
    
    # Créer une partie
    game = Game.objects.create(
        game_type='ludo',
        mode='competitive',
        player1=user1,
        player2=user2,
        status='playing',
        bet_amount=10,
        game_data=create_competitive_ludo_game()
    )
    
    # Configurer les couleurs
    game.game_data['player_colors'] = {
        str(user1.id): 'red',
        str(user2.id): 'blue'
    }
    game.game_data['current_player'] = 'red'
    
    # Placer manuellement des pions pour tester la capture
    pieces = game.game_data.get('pieces', [])
    
    # Mettre un pion rouge en position 5
    # Mettre un pion bleu en position 5 (sera capturé)
    for piece in pieces:
        if piece['color'] == 'red' and piece['id'] == 'red-0':
            piece['position'] = 3  # Position avant capture
            piece['isInPlay'] = True
        elif piece['color'] == 'blue' and piece['id'] == 'blue-0':
            piece['position'] = 5  # Position où le rouge va arriver
            piece['isInPlay'] = True
    
    game.save()
    
    print(f"✅ Partie créée: {game.id}")
    print(f"   Pion rouge en position 3")
    print(f"   Pion bleu en position 5 (cible)")
    
    # Simuler un lancer qui amène le rouge en position 5
    print("\n📍 TEST: Déplacer le rouge pour capturer le bleu")
    game.game_data['current_dice_value'] = 2
    game.save()
    
    # Calculer les mouvements légaux
    legal_moves = game.calculate_legal_moves('red', 2)
    print(f"   Mouvements légaux: {legal_moves}")
    
    # Déplacer le pion rouge
    success = game.process_ludo_piece_move(user1, 'red-0', 2)
    
    if success:
        # Vérifier la capture
        pieces = game.game_data.get('pieces', [])
        blue_piece = next((p for p in pieces if p['id'] == 'blue-0'), None)
        
        print(f"\n✅ Déplacement réussi!")
        print(f"   Position du pion bleu après: {blue_piece['position']}")
        print(f"   isInPlay du pion bleu: {blue_piece.get('isInPlay')}")
        
        if blue_piece and blue_piece['position'] == -1 and not blue_piece.get('isInPlay'):
            print("\n✅ TEST RÉUSSI: Le pion bleu a été capturé et renvoyé à la maison!")
        else:
            print("\n❌ TEST ÉCHOUÉ: Le pion bleu n'a pas été capturé correctement")
    else:
        print("❌ Échec du déplacement")
    
    # Nettoyer
    game.delete()
    print("\n🧹 Partie de test supprimée")


if __name__ == '__main__':
    print("\n🧪 TESTS DES CORRECTIONS LUDO")
    print("="*60)
    
    try:
        test_six_replay()
        test_capture()
        
        print("\n" + "="*60)
        print("✅ TOUS LES TESTS TERMINÉS")
        print("="*60 + "\n")
    except Exception as e:
        logger.error(f"❌ Erreur lors des tests: {e}", exc_info=True)
        sys.exit(1)
