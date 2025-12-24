# Mise à jour des Règles Ludo Compétitif

## Date: 17 Décembre 2025

### Nouvelles Règles Implémentées

#### 1. ✅ CAPTURE EN ARRIÈRE
**Fonctionnement:**
- Un pion peut capturer en avançant OU en reculant
- La vérification se fait sur la position EXACTE uniquement
- Pas de direction privilégiée

**Code:** `models.py` - fonction `check_captures()`

---

#### 2. 🚧 MUR AU PORTAIL (2 pions)
**Fonctionnement:**
- 2 pions ou plus de même couleur au portail = MUR
- Le mur BLOQUE le passage de l'adversaire
- Positions de portail (sortie maison):
  - Position 0: Rouge
  - Position 13: Vert
  - Position 26: Jaune
  - Position 39: Bleu

**Protection du mur:**
- Un mur au portail NE PEUT PAS être capturé
- L'adversaire doit casser le mur pour passer

**Code:** `models.py` - fonctions `is_wall_position()` et `check_captures()`

---

#### 3. ⚔️ PIONS EMPILÉS CAPTURABLES
**Fonctionnement:**
- Plusieurs pions de même couleur sur une case NORMALE = tous capturables ensemble
- **EXCEPTION:** Les murs au portail (2+ pions) NE peuvent PAS être capturés

**Distinction importante:**
- **Case normale** avec 2 pions → Capturables ensemble
- **Portail** avec 2 pions → MUR (non capturable)

**Code:** `models.py` - fonction `check_captures()`

---

#### 4. 🏠 CAPTURE → PIONS RESTENT CHEZ L'ADVERSAIRE
**Fonctionnement:**
- Quand un pion est capturé, il va à la BASE de celui qui a capturé
- Conceptuellement: le pion est "prisonnier" chez l'adversaire
- Implémentation: position = -1 (base), mais appartient à l'adversaire qui a capturé

**Changement par rapport à avant:**
- AVANT: Pion capturé → retourne à SA propre base
- MAINTENANT: Pion capturé → va à la base de CELUI QUI CAPTURE

**Code:** `models.py` - fonction `check_captures()` avec nouveau message de log

---

#### 5. 💥 CASSER UN MUR
**Conditions requises:**
1. Avoir fait **2 SIX CONSÉCUTIFS** dans le même tour
2. Le dé actuel doit faire tomber **EXACTEMENT** sur la case du mur

**Exemple:**
```
Position actuelle: 8
Mur vert au portail: position 13
Historique: 6, 6, ? 

Si le 3e dé = 5 → Tombe exactement sur 13 → MUR CASSÉ! ✅
Si le 3e dé = 4 → Ne tombe pas exactement → BLOQUÉ ❌
Si historique = 6, 4, 6 → Pas 2 six consécutifs → BLOQUÉ ❌
```

**Tracking:**
- `consecutive_sixes`: Compteur de six consécutifs
- Reset à 0 quand on lance un autre nombre
- Reset à 0 quand le tour change

**Code:** 
- `models.py` - fonction `can_break_wall()`
- `models.py` - tracking dans `process_ludo_dice_roll()` et `process_ludo_piece_move()`

---

#### 6. 🛡️ POSITIONS DE SÉCURITÉ
**Cases protégées (aucune capture possible):**
- Position 10: Avant entrée couloir rouge
- Position 23: Avant entrée couloir vert
- Position 36: Avant entrée couloir jaune
- Position 49: Avant entrée couloir bleu

**Note:** Les portails (0, 13, 26, 39) ne sont PLUS des cases de sécurité automatiques. 
Protection uniquement si MUR présent.

**Code:** `models.py` - fonction `check_captures()`

---

## Résumé des Modifications de Code

### Fichiers modifiés:

1. **`backend/apps/games/models.py`**
   - Nouvelle fonction: `is_wall_position(position, color)`
   - Nouvelle fonction: `can_break_wall(moving_color, target_position, dice_value, current_position)`
   - Fonction modifiée: `check_captures(moving_color, position)` - implémentation complète des nouvelles règles
   - Fonction modifiée: `process_ludo_piece_move()` - vérification des murs avant mouvement
   - Fonction modifiée: `calculate_legal_moves()` - vérification des murs dans les mouvements légaux
   - Tracking amélioré: `consecutive_sixes` pour la règle du mur

2. **`backend/apps/games/game_logic/ludo_competitive.py`**
   - Documentation mise à jour avec toutes les règles spéciales

---

## Tests Recommandés

### Test 1: Mur au Portail
1. Placer 2 pions rouges au portail rouge (position 0)
2. Tenter de passer avec un pion vert
3. ✅ Résultat attendu: Mouvement bloqué

### Test 2: Casser un Mur
1. Créer un mur vert au portail (position 13)
2. Pion rouge à position 8
3. Lancer: 6, 6, 5
4. ✅ Résultat attendu: Mur cassé (2 six consécutifs + tombe exactement sur 13)

### Test 3: Pions Empilés Capturables
1. Placer 2 pions verts sur position 20 (case normale)
2. Déplacer un pion rouge sur position 20
3. ✅ Résultat attendu: Les 2 pions verts sont capturés

### Test 4: Mur Non Capturable
1. Créer un mur bleu au portail (position 39, avec 2 pions)
2. Déplacer un pion rouge sur position 39
3. ✅ Résultat attendu: Mouvement bloqué, pas de capture

### Test 5: Capture en Arrière
1. Pion rouge à position 25
2. Pion vert à position 20
3. Déplacer pion rouge en arrière de 5 cases
4. ✅ Résultat attendu: Pion vert capturé

---

## Migration

**Aucune migration de base de données requise** - Les changements sont uniquement dans la logique de jeu.

Les parties en cours continueront de fonctionner avec les nouvelles règles appliquées immédiatement.

---

## Compatibilité

- ✅ Compatible avec les parties existantes
- ✅ Fonctionne avec n'importe quelles combinaisons de couleurs
- ✅ Maintient le système de timer et scoring existant
- ✅ Conserve toutes les règles Ludo classiques précédentes
