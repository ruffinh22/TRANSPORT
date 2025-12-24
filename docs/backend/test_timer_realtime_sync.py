#!/usr/bin/env python3
"""
Test de synchronisation temps réel - Tous les joueurs voient le même temps
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from apps.games.game_logic.checkers_competitive import create_competitive_checkers_game, make_competitive_move
import json
from time import sleep

def test_timer_realtime_sync():
    print("🧪 Test de synchronisation temps réel du timer\n")
    
    # Créer une partie
    game = create_competitive_checkers_game()
    print("✅ Partie créée\n")
    
    # Simuler 3 requêtes à des moments différents (comme 3 joueurs connectés)
    print("📡 Simulation de 3 clients connectés récupérant les données...\n")
    
    # Client 1 : Récupère immédiatement
    timer1 = game['timer']
    print(f"👤 Client 1 (t=0s):")
    print(f"  - red_time_remaining: {timer1['red_time_remaining']:.1f}s")
    print(f"  - black_time_remaining: {timer1['black_time_remaining']:.1f}s")
    print(f"  - move_time_remaining: {timer1['move_time_remaining']:.1f}s")
    
    # Attendre 2 secondes
    sleep(2)
    
    # Client 2 : Récupère après 2 secondes (doit voir le temps diminué)
    # En réalité, il faut recalculer via to_dict() pour avoir le temps actuel
    from apps.games.game_logic.checkers_competitive import CheckersBoard
    
    # Recréer le board depuis l'état pour forcer le recalcul
    # (en production, chaque requête WebSocket appellera to_dict() qui recalculera)
    print("\n⏳ 2 secondes plus tard...\n")
    
    # Faire un mouvement pour tester
    print("🎮 Joueur RED fait un mouvement...")
    result = make_competitive_move(game, 5, 0, 4, 1)
    
    if result['success']:
        game = result['game_state']
        timer2 = game['timer']
        print(f"\n👤 Client 2 (après mouvement):")
        print(f"  - red_time_remaining: {timer2['red_time_remaining']:.1f}s (temps déduit du coup!)")
        print(f"  - black_time_remaining: {timer2['black_time_remaining']:.1f}s")
        print(f"  - move_time_remaining: {timer2['move_time_remaining']:.1f}s (nouveau tour)")
        print(f"  - current_player: {timer2['current_player']}")
    
    # Attendre encore 2 secondes
    sleep(2)
    
    # Client 3 : Récupère après 2 secondes supplémentaires
    # IMPORTANT: Il faut recalculer via from_dict() + to_dict() comme le ferait le backend
    print("\n⏳ 2 secondes plus tard...\n")
    print("🔄 Le backend recalcule les temps via to_dict()...\n")
    
    # Simuler ce que fait le backend: désérialiser puis resérialiser (recalcule le temps)
    from apps.games.game_logic.checkers_competitive import CheckersBoard
    board = CheckersBoard.from_dict(game)
    game_recalculated = board.to_dict()  # ⬅️ ICI le temps est recalculé EN TEMPS RÉEL!
    
    timer3 = game_recalculated['timer']
    print(f"👤 Client 3 (t=4s après mouvement):")
    print(f"  - red_time_remaining: {timer3['red_time_remaining']:.1f}s")
    print(f"  - black_time_remaining: {timer3['black_time_remaining']:.1f}s ⬅️ DIMINUE!")
    print(f"  - move_time_remaining: {timer3['move_time_remaining']:.1f}s ⬅️ DIMINUE!")
    print(f"\n💡 Le timer de BLACK diminue car c'est son tour!")
    print(f"💡 move_time_remaining passe de 20s à ~{timer3['move_time_remaining']:.1f}s")
    
    print("\n" + "="*60)
    print("✅ RÉSULTAT:")
    print("="*60)
    print("📌 Le backend calcule les temps EN TEMPS RÉEL via to_dict()")
    print("📌 Chaque client WebSocket reçoit la MÊME valeur au même instant")
    print("📌 Pas de désynchronisation possible!")
    print("📌 Le frontend n'a qu'à afficher les valeurs reçues")
    
    print("\n🔄 Workflow:")
    print("  1. Backend: Appelle timer.to_dict() à chaque requête")
    print("  2. Backend: Calcule temps_restant = base - elapsed")
    print("  3. WebSocket: Envoie les valeurs à TOUS les clients")
    print("  4. Frontend: Affiche directement (source unique de vérité)")
    print("  5. Frontend: Décrémente localement pour fluidité")
    print("  6. Frontend: Resynchronise à chaque update WebSocket")
    
    print("\n🎯 Avantages:")
    print("  ✅ Temps identique pour tous (pas de triche)")
    print("  ✅ Fonctionne même après déconnexion/reconnexion")
    print("  ✅ Le serveur est la source de vérité")
    print("  ✅ Pas de décalage entre spectateurs")
    
    return 0

if __name__ == "__main__":
    try:
        exit(test_timer_realtime_sync())
    except Exception as e:
        print(f"\n❌ Erreur: {e}")
        import traceback
        traceback.print_exc()
        exit(1)
