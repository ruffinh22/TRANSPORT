# Système de Capture Ludo - Explication Complète

## 🎯 Règle Implémentée

**Quand Blue capture Vert:**
1. Le pion vert va à `position = -1` (base)
2. Le pion vert reçoit `captured_by = 'blue'` 
3. Le pion vert garde sa `color = 'green'`

## ✅ Comment ça Fonctionne

### Capture (par Blue)
```python
piece['position'] = -1          # Retour à la base
piece['isInPlay'] = False       # Plus en jeu
piece['captured_by'] = 'blue'   # Prisonnier chez blue
# piece['color'] reste 'green'  # Garde sa vraie couleur
```

### Sortie (par Green avec un 6)
```python
# Quand c'est le tour de Green:
if dice_value == 6 and piece['position'] == -1 and piece['color'] == 'green':
    # Le pion VERT sort depuis SA position de départ (13)
    new_position = start_positions['green']  # = 13
    piece['position'] = 13
    piece['isInPlay'] = True
    # piece['captured_by'] peut être effacé ou gardé pour stats
```

## 🔄 Cycle Complet

### Exemple: Blue capture Vert

**Avant capture:**
```json
{
  "id": "green-0",
  "color": "green",
  "position": 25,
  "isInPlay": true
}
```

**Blue arrive sur position 25 → CAPTURE!**
```json
{
  "id": "green-0",
  "color": "green",
  "position": -1,
  "isInPlay": false,
  "captured_by": "blue"  // ✅ NOUVEAU
}
```

**Green fait un 6 → SORTIE!**
```json
{
  "id": "green-0",
  "color": "green",
  "position": 13,         // Position de départ de GREEN (pas de blue!)
  "isInPlay": true,
  "captured_by": "blue"   // Optionnel: peut rester pour statistiques
}
```

## 📊 Points Importants

1. **Le pion garde sa couleur d'origine** → Toujours filtré par `piece['color'] == 'green'`
2. **Le pion est à position -1** → Dans la base
3. **captured_by indique le capteur** → Pour statistiques/UI
4. **Green peut le sortir** → Avec un 6, comme un pion normal
5. **Il sort depuis SA position** → start_positions['green'] = 13

## 🎨 Affichage Frontend (Recommandé)

```javascript
// Dans la base de Blue, afficher:
// - Pions bleus normaux (color='blue', position=-1, !captured_by)
// - Pions verts capturés (color='green', position=-1, captured_by='blue')

const bluePiecesInBase = pieces.filter(p => 
  p.position === -1 && 
  (p.color === 'blue' || p.captured_by === 'blue')
);

// Afficher visuellement différemment:
// - Pion bleu: 🔵
// - Pion vert capturé par blue: 🟢 (avec badge 🔵 ou chaînes ⛓️)
```

## ✅ Vérifications Automatiques

Le système vérifie automatiquement:
- ✅ Seul GREEN peut faire sortir un pion green (même capturé)
- ✅ Il faut un 6 pour sortir
- ✅ Le pion sort depuis la position de départ de GREEN
- ✅ Le compteur de captures de BLUE augmente
- ✅ Les points sont attribués correctement

## 🐛 Debug

Pour vérifier si ça marche:
```python
# Logs à surveiller:
logger.info(f"⚔️ CAPTURE! {moving_color} captures {piece_color} piece {piece_id}")
logger.info(f"   → Pion {piece_color} envoyé à la BASE de {moving_color}")

# Quand green joue un 6:
logger.info(f"🏠 Piece {piece_id} can exit to position {start_pos}")
# start_pos devrait être 13 pour green, pas 39 (blue)
```

## 📝 Code Clé

### Capture (models.py ligne ~1640)
```python
piece['position'] = -1
piece['isInPlay'] = False
piece['captured_by'] = moving_color  # ✅ NOUVEAU
```

### Sortie (calculate_new_position, ligne ~1487)
```python
if current_pos == -1 and dice_value == 6:
    return start_positions[color]  # Utilise la couleur du PION, pas du joueur
```

### Filtre des pions (calculate_legal_moves, ligne ~1425)
```python
if piece.get('color') != player_color:
    continue  # Ne considère que les pions de SA couleur
```

## ✨ Résultat Final

- ✅ Blue capture vert → pion vert va en base (conceptuellement "chez blue")
- ✅ Green fait un 6 → pion vert sort depuis position 13 (départ de green)
- ✅ Le pion vert continue normalement son chemin
- ✅ Les statistiques trackent qui a capturé qui
