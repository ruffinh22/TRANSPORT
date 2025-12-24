# 🏁 Intégration du Jeu de Dames Compétitif 10x10

## ✅ Statut : Intégration Complétée

Le jeu de dames compétitif 10x10 avec toutes les règles officielles est maintenant **complètement intégré** dans l'application Django.

---

## 📁 Architecture

### 1. **Logique de Jeu** (`checkers_competitive.py`)
**Fichier** : `backend/apps/games/game_logic/checkers_competitive.py`

**Classes principales** :
- `Color` : Énumération des couleurs (RED, BLACK)
- `PieceType` : Type de pièce (MAN = pion, KING = dame)
- `Position` : Position sur le plateau (row, col)
- `Move` : Représentation d'un mouvement avec captures et points
- `CheckersPiece` : Pièce du jeu avec ses propriétés
- `PlayerScore` : Score d'un joueur avec détails des points
- `GameTimer` : Gestion du temps (20s par coup, 5min global)
- `CheckersBoard` : Plateau de jeu avec toute la logique

**Fonctions publiques** :
```python
# Créer une nouvelle partie
game = create_competitive_checkers_game()

# Obtenir les mouvements légaux
moves = get_competitive_legal_moves(game, row, col)

# Effectuer un mouvement
result = make_competitive_move(game, from_row, from_col, to_row, to_col)

# Vérifier si la partie est terminée
is_over, winner, details = check_competitive_game_over(game)
```

---

### 2. **Modèle Django** (`models.py`)
**Fichier** : `backend/apps/games/models.py`

**Méthodes modifiées** :

#### `initialize_checkers()` (ligne ~292)
- Crée une nouvelle partie compétitive au démarrage
- Initialise le timer et les scores
- Mappe les joueurs aux couleurs (player1 = rouge, player2 = noir)

#### `process_checkers_move()` (ligne ~1692)
- Valide le tour du joueur
- Exécute le mouvement avec le moteur compétitif
- Met à jour les scores et le temps
- Vérifie les conditions de victoire
- Traite les gains si partie terminée

---

### 3. **API REST** (`views.py`)
**Fichier** : `backend/apps/games/views.py`

**Endpoint existant** : `POST /api/games/{id}/move/`

**Flow complet** :
```
Frontend → POST /api/games/{id}/move/
    ↓
GameViewSet.move() (ligne 300)
    ↓
Game.make_move() (ligne 491)
    ↓
Game.process_checkers_move() (ligne 1692)
    ↓
make_competitive_move() from checkers_competitive.py
    ↓
Retour JSON avec game_state mis à jour
```

---

## 🎮 Règles Implémentées

### ✅ Règles de Base
- [x] Plateau 10x10 (100 cases, 50 cases noires utilisées)
- [x] 20 pions par joueur
- [x] Déplacement diagonal des pions (avant seulement)
- [x] Déplacement diagonal des dames (toutes directions, illimité)
- [x] Promotion en dame à la dernière rangée

### ✅ Règles de Capture
- [x] Captures obligatoires
- [x] Captures multiples en chaîne
- [x] Priorité au chemin qui capture le plus de pièces
- [x] Dame peut capturer à distance

### ✅ Système de Points
- [x] Capture pion : **+1 point**
- [x] Capture dame : **+3 points**
- [x] Promotion en dame : **+2 points**
- [x] Coup multiple (bonus) : **+1 point**

### ✅ Gestion du Temps
- [x] **20 secondes** par coup
- [x] **5 minutes** (300s) timer global
- [x] Perte automatique si temps dépassé
- [x] Victoire au score si timer global expire

### ✅ Conditions de Victoire
- [x] Élimination de toutes les pièces adverses
- [x] Blocage complet de l'adversaire
- [x] Abandon
- [x] Timeout (plus de points gagne)
- [x] Match nul si égalité de points

---

## 🔌 Utilisation dans l'API

### 1. Créer une Partie de Dames
```http
POST /api/v1/games/
{
  "game_type": "dames_competitive",
  "bet_amount": 1000,
  "currency": "XOF"
}
```

### 2. Démarrer la Partie
```http
POST /api/v1/games/{game_id}/start/
```
→ Initialise le plateau 10x10 avec 20 pions par joueur

### 3. Faire un Mouvement
```http
POST /api/v1/games/{game_id}/move/
{
  "action": "MOVE_PIECE",
  "from": [6, 1],    // Position [row, col]
  "to": [5, 0]       // Position [row, col]
}
```

**Réponse** :
```json
{
  "success": true,
  "game": {
    "id": "...",
    "status": "playing",
    "game_data": {
      "board": [...],
      "current_player": "black",
      "red_score": {"points": 1, "captures": 1},
      "black_score": {"points": 0, "captures": 0},
      "timer": {
        "red_time_remaining": 285,
        "black_time_remaining": 300,
        "move_time_limit": 20,
        "global_time_limit": 300
      }
    }
  }
}
```

### 4. Vérifier l'État du Jeu
```http
GET /api/v1/games/{game_id}/
```

---

## 🧪 Tests

**Fichier de test** : `backend/test_checkers_competitive.py`

```bash
cd /var/www/html/rumo_rush/backend
python3 test_checkers_competitive.py
```

**Résultat attendu** :
```
============================================================
🏁 Test du jeu de Dames Compétitif 10x10
============================================================
✅ Plateau: 10x10
✅ Pièces rouges: 20/20
✅ Pièces noires: 20/20
✅ Timer global: 300s
✅ Timer par coup: 20s
✅ Mouvement réussi!
```

---

## 📊 Structure des Données

### Format du `game_data`
```python
{
    "size": 10,
    "board": [[None, {...}, None, {...}, ...], ...],  # 10x10
    "current_player": "red",  # ou "black"
    
    "red_score": {
        "points": 0,
        "captures": 0,
        "promotions": 0,
        "multi_captures": 0
    },
    
    "black_score": {
        "points": 0,
        "captures": 0,
        "promotions": 0,
        "multi_captures": 0
    },
    
    "timer": {
        "global_time_limit": 300,
        "move_time_limit": 20,
        "red_time_remaining": 300,
        "black_time_remaining": 300,
        "last_move_time": "2025-11-28T10:00:00",
        "game_start_time": "2025-11-28T10:00:00"
    },
    
    "player_mapping": {
        "red": "uuid-player1",
        "black": "uuid-player2"
    },
    
    "move_history": [...]
}
```

### Format d'une Pièce
```python
{
    "color": "red",           # ou "black"
    "piece_type": "man",      # ou "king"
    "row": 6,
    "col": 1,
    "is_king": false
}
```

---

## 🚀 Prochaines Étapes (Optionnel)

### Frontend
- [ ] Afficher le score en temps réel
- [ ] Afficher le timer (countdown)
- [ ] Highlight des mouvements légaux
- [ ] Animation des captures
- [ ] Son lors des captures/promotions

### Backend
- [ ] WebSocket pour mises à jour temps réel
- [ ] Historique des mouvements détaillé
- [ ] Rejeu de parties
- [ ] Tournois de dames
- [ ] Classement ELO

---

## 📝 Notes Importantes

1. **Mapping des Joueurs** :
   - Player1 (créateur) = Pions **ROUGES**
   - Player2 (invité) = Pions **NOIRS**

2. **Timer** :
   - Démarre automatiquement au `start_game()`
   - Compte à rebours par coup ET global
   - Fin auto si timeout

3. **Compatibilité** :
   - Conserve l'ancien moteur `checkers.py` pour compatibilité
   - Utilise `checkers_competitive.py` pour nouvelles parties
   - Détection automatique du moteur selon `game_data`

---

## ✅ Validation

- [x] Tests unitaires passent
- [x] Intégration avec models.py
- [x] Intégration avec views.py
- [x] API REST fonctionnelle
- [x] Documentation complète

**Statut** : ✨ **Production Ready** ✨
