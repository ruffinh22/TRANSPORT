# 🏁 Règles Officielles - Dames Compétitives (10x10)

## 📋 Vue d'ensemble

Implementation complète des règles officielles des Dames internationales (10×10) avec système de points compétitif et gestion du temps pour RUMO RUSH.

---

## 🎯 Objectif du jeu

**Gagner la partie en :**
- Capturant tous les pions adverses
- Bloquant complètement l'adversaire (aucun mouvement possible)
- Ayant le score le plus élevé au timeout global

---

## 🎲 Mise en place

### Plateau
- **Dimensions** : 10 × 10 cases
- **Cases jouables** : Seulement les cases **noires** (50 cases)
- **Cases blanches** : Non utilisées

### Pièces initiales
- **Chaque joueur** : 20 pions
- **Rouge (light)** : 4 dernières rangées (rangées 6-9)
- **Noir (dark)** : 4 premières rangées (rangées 0-3)

### Notation des positions
- **Colonnes** : a-j (gauche à droite)
- **Rangées** : 1-10 (bas en haut)
- Exemple : `a1`, `e5`, `j10`

---

## 🚶 Déplacement des pièces

### Pion simple
- **Direction** : Diagonale vers l'avant uniquement
- **Distance** : 1 case à la fois
- **Restriction** : Ne peut pas reculer

### Dame (Roi)
- **Direction** : Toutes les diagonales (avant ET arrière)
- **Distance** : Autant de cases qu'elle veut
- **Avantage** : Peut se déplacer sur plusieurs cases vides

### Promotion
Un pion devient **dame** lorsqu'il atteint la dernière rangée adverse :
- Rouge : Atteint la rangée 0 (haut du plateau)
- Noir : Atteint la rangée 9 (bas du plateau)

---

## 🎯 Règles de capture

### ⚠️ CAPTURE OBLIGATOIRE
**Si un joueur peut capturer, il DOIT le faire !**

### Capture simple (Pion)
- Sauter par-dessus une pièce adverse en diagonale
- Atterrir sur la case vide juste derrière
- La pièce capturée est retirée du plateau

### Capture à distance (Dame)
- Peut capturer une pièce adverse à n'importe quelle distance
- Peut atterrir sur n'importe quelle case libre après la pièce capturée
- Exemple : Dame en `a1` capture pion en `c3` et peut atterrir en `d4`, `e5`, `f6`, etc.

### Captures multiples (Enchaînement)
- **Obligatoire** : Si après une capture, d'autres captures sont possibles, elles doivent être faites dans le même tour
- Le joueur **ne peut pas choisir** de s'arrêter entre deux captures
- Peut changer de direction entre chaque capture
- Les pièces capturées sont retirées **après** l'enchaînement complet

### Priorité des captures
**Règle du maximum** :
- Si plusieurs chemins de capture existent, choisir celui qui capture le **plus grand nombre** de pièces
- En cas d'égalité, n'importe quel chemin maximal peut être choisi
- La qualité (pion vs dame) n'affecte pas cette règle, seulement la quantité

---

## ⏱️ Gestion du temps

### Temps par coup
- **Limite** : 20 secondes par mouvement
- **Dépassement** : Le joueur perd son tour automatiquement
- L'adversaire joue immédiatement

### Timer global
- **Durée totale** : 5 minutes (300 secondes)
- Temps partagé entre tous les coups du joueur
- **À 0 seconde** : Fin de partie

### Fin par timeout
Quand le chrono global atteint 0 :
- Le joueur avec le **plus de points** gagne
- En cas d'égalité : **Match nul**

---

## 📊 Système de points compétitif

### Points par action

| Action | Points |
|--------|--------|
| Capture d'un **pion** | +1 |
| Capture d'une **dame** | +3 |
| Promotion en dame | +2 |
| Coup multiple (≥2 captures) | +1 bonus |

### Exemples de calcul

#### Exemple 1 : Capture simple
```
Pion capture 1 pion adverse
→ 1 point
```

#### Exemple 2 : Capture multiple
```
Pion capture 3 pions adverses en un coup
→ (1 + 1 + 1) + 1 bonus = 4 points
```

#### Exemple 3 : Capture avec promotion
```
Pion capture 1 pion et atteint la dernière rangée
→ 1 (capture) + 2 (promotion) = 3 points
```

#### Exemple 4 : Dame capture avec multi
```
Dame capture 2 pions + 1 dame
→ (1 + 1 + 3) + 1 bonus = 6 points
```

### Score final
**Score = Total de tous les points gagnés pendant la partie**

Permet de déterminer le gagnant en cas de :
- Timeout global
- Abandon
- Blocage mutuel

---

## 🏆 Conditions de victoire

### Victoire immédiate
1. **Élimination** : Tous les pions adverses capturés
2. **Blocage** : L'adversaire ne peut plus jouer aucun coup légal
3. **Abandon** : L'adversaire abandonne

### Victoire par timeout
- **Timeout global** (5 min écoulées) : Gagnant = score le plus élevé
- **Timeout joueur** (temps individuel épuisé) : Gagnant = adversaire

### Match nul
- Scores égaux au timeout global
- Situation de blocage mutuel (rare)

---

## 🎮 Intégration dans RUMO RUSH

### Création d'une partie
```python
from apps.games.game_logic.checkers_competitive import create_competitive_checkers_game

game_state = create_competitive_checkers_game()
# Le timer démarre automatiquement
```

### Effectuer un mouvement
```python
from apps.games.game_logic.checkers_competitive import make_competitive_checkers_move

move_data = {
    'from': {'row': 7, 'col': 0},  # Position de départ
    'to': {'row': 6, 'col': 1}      # Position d'arrivée
}

new_state, success, message = make_competitive_checkers_move(game_state, move_data)

if success:
    print(f"✅ {message}")
    print(f"Points gagnés: {new_state['red_score']['points']}")
else:
    print(f"❌ Erreur: {message}")
```

### Obtenir les coups légaux
```python
from apps.games.game_logic.checkers_competitive import get_competitive_legal_moves

legal_moves = get_competitive_legal_moves(game_state, row=7, col=0)

for move in legal_moves:
    print(f"Vers ({move['to']['row']}, {move['to']['col']})")
    print(f"  Captures: {len(move['captured'])} pièce(s)")
    print(f"  Points: {move['points']}")
    if move['is_multi_capture']:
        print(f"  🔥 Multi-capture!")
```

### Vérifier fin de partie
```python
from apps.games.game_logic.checkers_competitive import check_competitive_game_over

is_over, winner, details = check_competitive_game_over(game_state)

if is_over:
    print(f"🏁 Partie terminée!")
    print(f"Gagnant: {winner}")
    print(f"Raison: {details['reason']}")
    print(f"Score rouge: {details['red_score']['points']}")
    print(f"Score noir: {details['black_score']['points']}")
```

---

## 📈 État du jeu

### Structure `game_state`
```python
{
    'board': [[...], ...],           # Plateau 10x10
    'current_player': 'red'|'black',
    'size': 10,
    
    # Scores
    'red_score': {
        'points': 15,
        'pieces_captured': 8,
        'kings_captured': 2,
        'promotions': 3,
        'multi_captures': 2
    },
    'black_score': { ... },
    
    # Timer
    'timer': {
        'move_time_limit': 20,
        'global_time_limit': 300,
        'red_time_remaining': 245.5,
        'black_time_remaining': 280.3,
        'global_timeout': False
    },
    
    # État
    'is_game_over': False,
    'winner': None,
    'mandatory_capture_piece': None
}
```

---

## 🔧 Différences avec la version classique

| Aspect | Classique (8x8) | Compétitive (10x10) |
|--------|----------------|---------------------|
| Taille plateau | 8×8 (32 cases) | 10×10 (50 cases) |
| Pions par joueur | 12 | 20 |
| Rangées initiales | 3 | 4 |
| Timer par coup | Non | 20 secondes |
| Timer global | Non | 5 minutes |
| Système de points | Non | Oui (+1/+3/+2/+1) |
| Victoire par score | Non | Oui (timeout) |

---

## 📝 Notes d'implémentation

### Optimisations
- Calcul automatique des captures maximales
- Détection des enchaînements récursifs
- Validation stricte des règles
- Gestion précise du temps

### Améliorations futures
- [ ] Historique détaillé des coups avec replay
- [ ] Analyse des positions (évaluation du plateau)
- [ ] Suggestions de meilleurs coups
- [ ] Détection de répétitions (règle des 3 coups)
- [ ] Sauvegarde/restauration de parties
- [ ] Mode spectateur temps réel

---

## 🐛 Tests et validation

Pour tester l'implémentation :

```python
# Test des captures multiples
def test_multi_capture():
    game = create_competitive_checkers_game()
    # Setup position spécifique...
    move = make_competitive_checkers_move(game, move_data)
    assert move[0]['red_score']['points'] == 4  # 3 captures + 1 bonus

# Test du timeout
def test_timeout():
    game = create_competitive_checkers_game()
    # Attendre 301 secondes...
    is_over, winner, details = check_competitive_game_over(game)
    assert is_over == True
    assert details['reason'] == 'global_timeout'
```

---

## 📞 Support

Pour toute question ou bug :
- Backend : `apps/games/game_logic/checkers_competitive.py`
- Issues GitHub : [hounsounon-anselme/rumo_rush](https://github.com/hounsounon-anselme/rumo_rush)

---

**Version** : 1.0.0  
**Dernière mise à jour** : 28 novembre 2025  
**Auteur** : GitHub Copilot pour RUMO RUSH
