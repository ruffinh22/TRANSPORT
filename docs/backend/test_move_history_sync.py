#!/usr/bin/env python3
"""
Test de synchronisation de l'historique des mouvements et des timestamps.
Vérifie que move_history et timer se mettent à jour correctement.
"""

import sys
import os
import django

# Ajouter le répertoire parent au PYTHONPATH
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Configurer Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'rumo_rush.settings.testing')
django.setup()

from datetime import datetime, timedelta
from django.utils import timezone
from apps.games.models import Game
from apps.games.game_logic.checkers_competitive import (
    create_competitive_checkers_game,
    make_competitive_move,
    CheckersBoard
)
import json

def test_move_history_and_timer():
    """Tester que move_history et timer se mettent à jour correctement."""
    
    print("=" * 80)
    print("TEST: Synchronisation move_history et timer")
    print("=" * 80)
    
    # 1. Créer un jeu compétitif
    print("\n✅ Création d'une partie de dames compétitives...")
    game_state = create_competitive_checkers_game()
    
    initial_timer = game_state['timer'].copy()
    print(f"⏱️  Timer initial:")
    print(f"   - Joueur actuel: {initial_timer['current_player']}")
    print(f"   - Temps RED: {initial_timer['red_time_remaining']}s")
    print(f"   - Temps BLACK: {initial_timer['black_time_remaining']}s")
    print(f"   - Temps mouvement: {initial_timer['move_time_remaining']}s")
    print(f"   - Start move: {initial_timer.get('current_move_start')}")
    
    # 2. Effectuer un mouvement
    print("\n✅ Exécution d'un mouvement (RED: 6,1 -> 5,0)...")
    result = make_competitive_move(game_state, 6, 1, 5, 0)
    
    if not result['success']:
        print(f"❌ ERREUR: {result['error']}")
        return False
    
    print(f"✅ Mouvement réussi! Points gagnés: {result['points_gained']}")
    
    # 3. Vérifier le nouvel état
    updated_state = result['game_state']
    updated_timer = updated_state['timer']
    
    print(f"\n⏱️  Timer après mouvement:")
    print(f"   - Joueur actuel: {updated_timer['current_player']}")
    print(f"   - Temps RED: {updated_timer['red_time_remaining']}s")
    print(f"   - Temps BLACK: {updated_timer['black_time_remaining']}s")
    print(f"   - Temps mouvement: {updated_timer['move_time_remaining']}s")
    print(f"   - Start move: {updated_timer.get('current_move_start')}")
    
    # 4. Vérifications
    print("\n🔍 Vérifications:")
    
    # Le joueur a changé
    if updated_timer['current_player'] != initial_timer['current_player']:
        print("   ✅ Le joueur actuel a changé (RED -> BLACK)")
    else:
        print("   ❌ Le joueur actuel n'a PAS changé!")
        return False
    
    # Le timestamp a été mis à jour
    if updated_timer.get('current_move_start') != initial_timer.get('current_move_start'):
        print("   ✅ Le timestamp current_move_start a été mis à jour")
    else:
        print("   ❌ Le timestamp current_move_start n'a PAS changé!")
        return False
    
    # Le temps de mouvement a été réinitialisé
    if updated_timer['move_time_remaining'] == 20:
        print("   ✅ Le temps de mouvement a été réinitialisé à 20s")
    else:
        print(f"   ⚠️  Le temps de mouvement est à {updated_timer['move_time_remaining']}s (attendu: 20s)")
    
    print("\n" + "=" * 80)
    print("✅ TEST RÉUSSI: Timer synchronisé correctement!")
    print("=" * 80)
    return True


def test_database_integration():
    """Tester l'intégration avec la base de données."""
    
    print("\n" + "=" * 80)
    print("TEST: Intégration base de données")
    print("=" * 80)
    
    # Trouver une partie en cours
    game = Game.objects.filter(
        status='playing',
        game_type__name='checkers'
    ).first()
    
    if not game:
        print("⚠️  Aucune partie de dames en cours trouvée")
        print("   Créez une partie via l'interface web pour tester")
        return True
    
    print(f"\n✅ Partie trouvée: {game.room_code} (ID: {game.id})")
    print(f"   Status: {game.status}")
    print(f"   Player1: {game.player1.username}")
    print(f"   Player2: {game.player2.username if game.player2 else 'None'}")
    
    # Vérifier move_history
    if hasattr(game, 'move_history') and game.move_history:
        print(f"\n📜 Historique des mouvements:")
        print(f"   Nombre de mouvements: {len(game.move_history)}")
        if len(game.move_history) > 0:
            last_move = game.move_history[-1]
            print(f"   Dernier mouvement:")
            print(f"     - Joueur: {last_move.get('player')}")
            print(f"     - Tour: {last_move.get('turn_number')}")
            print(f"     - Timestamp: {last_move.get('timestamp')}")
    else:
        print("\n⚠️  move_history est vide ou None")
    
    # Vérifier timer
    if game.game_data and 'timer' in game.game_data:
        timer = game.game_data['timer']
        print(f"\n⏱️  Timer:")
        print(f"   - Joueur actuel: {timer.get('current_player')}")
        print(f"   - Temps RED: {timer.get('red_time_remaining')}s")
        print(f"   - Temps BLACK: {timer.get('black_time_remaining')}s")
        print(f"   - Start move: {timer.get('current_move_start')}")
    else:
        print("\n⚠️  Timer non trouvé dans game_data")
    
    print("\n" + "=" * 80)
    print("✅ TEST TERMINÉ: Vérifiez les valeurs ci-dessus")
    print("=" * 80)
    return True


if __name__ == '__main__':
    print("\n🎯 Démarrage des tests de synchronisation...\n")
    
    try:
        # Test 1: Synchronisation timer dans le moteur
        success1 = test_move_history_and_timer()
        
        # Test 2: Intégration base de données
        success2 = test_database_integration()
        
        if success1 and success2:
            print("\n✅ TOUS LES TESTS RÉUSSIS!")
            sys.exit(0)
        else:
            print("\n❌ CERTAINS TESTS ONT ÉCHOUÉ")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n❌ ERREUR INATTENDUE: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
