# 📖 RÈGLES DES ÉCHECS - Guide Complet

## 🎯 Objectif du Jeu

**Mettre le roi adverse en échec et mat** : le roi est attaqué et n'a aucun moyen d'échapper à l'attaque.

---

## ♟️ Les Pièces et Leurs Mouvements

### 1. Le Roi (♔ ♚) - La pièce la plus importante

**Mouvement :**
- Se déplace d'**une seule case** dans toutes les directions (horizontale, verticale, diagonale)
- Ne peut JAMAIS se mettre en échec (sur une case attaquée par l'adversaire)

**Règles spéciales :**
- **Roque** : Coup spécial avec la tour (voir section dédiée)
- Le roi ne peut jamais être capturé, il doit être protégé à tout prix

**Exemples de mouvements :**
```
. . . . . . . .
. x x x . . . .
. x ♔ x . . . .
. x x x . . . .
. . . . . . . .
```

---

### 2. La Dame (♕ ♛) - La pièce la plus puissante

**Mouvement :**
- Se déplace dans **toutes les directions** (horizontale, verticale, diagonale)
- Peut parcourir **autant de cases qu'elle veut**
- Combine les mouvements de la tour et du fou

**Exemples de mouvements :**
```
x . . x . . . x
. x . x . . x .
. . x x . x . .
x x x ♕ x x x x  ← La dame peut aller partout !
. . x x . x . .
. x . x . . x .
x . . x . . . x
. . . x . . . .
```

---

### 3. La Tour (♖ ♜)

**Mouvement :**
- Se déplace **horizontalement** ou **verticalement**
- Peut parcourir **autant de cases qu'elle veut**

**Règles spéciales :**
- Participe au **roque** avec le roi

**Exemples de mouvements :**
```
. . . x . . . .
. . . x . . . .
. . . x . . . .
x x x ♖ x x x x  ← Lignes droites seulement
. . . x . . . .
. . . x . . . .
. . . x . . . .
. . . x . . . .
```

---

### 4. Le Fou (♗ ♝)

**Mouvement :**
- Se déplace **en diagonale uniquement**
- Peut parcourir **autant de cases qu'il veut**
- Un fou reste toujours sur la même couleur de case (clair ou foncé)

**Exemples de mouvements :**
```
x . . . . . . x
. x . . . . x .
. . x . . x . .
. . . ♗ x . . .  ← Diagonales seulement
. . x . x . . .
. x . . . x . .
x . . . . . x .
. . . . . . . x
```

---

### 5. Le Cavalier (♘ ♞)

**Mouvement :**
- Se déplace en **forme de "L"** : 2 cases dans une direction + 1 case perpendiculaire
- C'est la **seule pièce qui peut sauter** par-dessus d'autres pièces

**Exemples de mouvements :**
```
. . . . . . . .
. . x . x . . .
. x . . . x . .
. . . ♘ . . . .  ← 8 positions possibles
. x . . . x . .
. . x . x . . .
. . . . . . . .
```

---

### 6. Le Pion (♙ ♟)

**Mouvement normal :**
- Avance d'**une case** vers l'avant uniquement
- **Première fois** : peut avancer de **2 cases** d'un coup

**Capture :**
- Capture **en diagonale** d'une case (jamais tout droit)

**Règles spéciales :**
- **Promotion** : Arrivé en fin d'échiquier (8ème rangée), le pion se transforme en Dame, Tour, Fou ou Cavalier
- **Prise en passant** : Peut capturer un pion adverse qui vient d'avancer de 2 cases

**Exemples de mouvements :**
```
Pion blanc (♙) avance vers le haut :
. . . . . . . .
. . x . x . . .  ← Capture en diagonale
. . . ♙ . . . .
. . . x . . . .  ← Avance 1 case
. . . x . . . .  ← Avance 2 cases (1er coup)
```

---

## ⚔️ Règles Fondamentales

### 1. L'Échec (Check)

**Définition :**
Le roi est **en échec** quand il est attaqué par une pièce adverse.

**Obligation :**
Quand votre roi est en échec, vous **DEVEZ** :
1. **Déplacer le roi** hors de portée, OU
2. **Capturer** la pièce qui met en échec, OU
3. **Bloquer** l'attaque avec une autre pièce

**⚠️ Vous NE POUVEZ PAS jouer un coup qui laisse ou met votre roi en échec !**

**Exemple :**
```
♜ . . ♛ ♚ . . ♜  ← Roi noir en e8, Dame blanche en d8
. . . . . . . .      Le roi noir est EN ÉCHEC !
                     
Coups LÉGAUX pour les noirs :
- Kxd8 (capturer la dame avec le roi)
- Nxd8 (capturer avec cavalier)
- Rxd8 (capturer avec tour)

Coups ILLÉGAUX :
- b7-b5 (ne résout PAS l'échec)
- Kf8 (la dame contrôle f8)
```

---

### 2. L'Échec et Mat (Checkmate)

**Définition :**
Le roi est en échec et **aucun coup ne peut le sauver**.

**Résultat :** Le joueur qui met échec et mat **GAGNE** la partie !

**Exemple simple (Mat du Couloir) :**
```
♚ . . . . . . .  ← Roi noir en a8, coincé par ses pions
♟ ♟ . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
. . . . . . . .
♜ . . . . . ♔ .  ← Tour blanche en a1 : ÉCHEC ET MAT !

Le roi noir ne peut :
- Ni bouger (b8 et b7 bloqués par pions)
- Ni capturer la tour (trop loin)
- Ni bloquer (impossible, tour adjacent)
```

---

### 3. Le Pat (Stalemate)

**Définition :**
- Le joueur n'est **PAS en échec**
- MAIS il n'a **aucun coup légal** à jouer

**Résultat :** **MATCH NUL** (personne ne gagne)

**Exemple :**
```
. . . . . . . ♚  ← Roi noir en h8
. . . . . . ♔ .  ← Roi blanc en g7
. . . . . . . .
♛ . . . . . . .  ← Dame blanche en a6

Le roi noir n'est PAS en échec
MAIS : Toutes les cases (g8, h7) sont contrôlées
Aucun coup légal → PAT = Match nul
```

---

## 🎲 Coups Spéciaux

### 1. Le Roque (Castling)

**Principe :** Déplacer le roi de 2 cases vers une tour, et la tour saute par-dessus le roi.

**Types :**
- **Petit roque (O-O)** : Roi vers la tour côté roi (tour h)
- **Grand roque (O-O-O)** : Roi vers la tour côté dame (tour a)

**Conditions (TOUTES obligatoires) :**
1. Le roi n'a **jamais bougé**
2. La tour choisie n'a **jamais bougé**
3. **Aucune pièce** entre le roi et la tour
4. Le roi **n'est PAS en échec**
5. Le roi ne **traverse PAS** une case attaquée
6. Le roi n'**arrive PAS** sur une case attaquée

**Exemple - Petit roque blanc :**
```
Avant :                 Après :
♜ . . . ♚ . . ♜         ♜ . . . . ♜ ♚ .
. . . . . . . .   →     . . . . . . . .
                        
♖ . . . ♔ . . ♖         ♖ . . . . ♖ ♔ .
```

---

### 2. La Prise en Passant (En Passant)

**Situation :**
- Votre pion est sur la 5ème rangée (blanc) ou 4ème rangée (noir)
- Un pion adverse avance de **2 cases** et se retrouve **à côté** de votre pion

**Règle :**
Vous pouvez capturer ce pion **comme s'il n'avait avancé que d'une case**.

**⚠️ Important :** Ce coup doit être joué **immédiatement** au tour suivant, sinon vous perdez cette opportunité.

**Exemple :**
```
Situation :             Prise en passant :
. . . . . . . .         . . . . . . . .
. . ♙ ♟ . . . .   →     . . ♟ . . . .  ← Pion noir capture
. . . . . . . .         . . . . . . . .    et le pion blanc disparaît
```

---

### 3. La Promotion du Pion

**Règle :**
Quand un pion atteint la **dernière rangée** (8ème pour blanc, 1ère pour noir), il **doit** être transformé en :
- Dame (choix le plus courant) ♛
- Tour ♜
- Fou ♝
- Cavalier ♞

**⚠️ Il ne peut PAS rester pion ni devenir roi.**

**Exemple :**
```
♟ . . . . . . .  ← Pion blanc en a7
. . . . . . . .
                    Après a7-a8 :
♛ . . . . . . .  ← Devient une dame !
```

---

## 🏁 Fins de Partie

### 1. Victoire

**Échec et mat :** Le roi adverse ne peut échapper à l'attaque
- Le joueur qui mate **gagne la partie**

**Abandon :** Un joueur peut abandonner à tout moment
- L'adversaire **gagne automatiquement**

---

### 2. Match Nul (Draw)

**a) Pat (Stalemate) :**
- Joueur non en échec mais sans coup légal

**b) Matériel Insuffisant :**
- Roi contre Roi
- Roi + Fou contre Roi
- Roi + Cavalier contre Roi

**c) Règle des 50 coups :**
- 50 coups consécutifs sans capture ni mouvement de pion
- L'un des joueurs peut réclamer la nulle

**d) Répétition de position :**
- La même position se répète 3 fois
- L'un des joueurs peut réclamer la nulle

**e) Accord mutuel :**
- Les deux joueurs acceptent la nulle

---

### 3. Timeout (Partie avec pendule)

**Règle :**
- Chaque joueur a un temps limité (ex: 60 secondes par coup, 2h au total)
- Si le temps expire → **DÉFAITE par timeout**

**Dans Rumo Rush :**
- ⏱️ **60 secondes** par coup
- ⏱️ **7200 secondes (2h)** au total par joueur
- Si timeout → L'adversaire gagne

---

## 🎯 Stratégies de Base

### Phases du Jeu

**1. Ouverture (coups 1-10) :**
- Contrôler le centre (cases e4, d4, e5, d5)
- Développer les pièces (cavaliers, fous)
- Roquer rapidement pour protéger le roi

**2. Milieu de Partie :**
- Attaquer les faiblesses adverses
- Coordonner les pièces
- Chercher des tactiques (fourchettes, clouages, etc.)

**3. Finale :**
- Activer le roi (il devient une pièce d'attaque)
- Promouvoir les pions
- Chercher l'échec et mat

---

### Valeur Relative des Pièces

Pour évaluer les échanges :
- **Pion** : 1 point
- **Cavalier** : 3 points
- **Fou** : 3 points
- **Tour** : 5 points
- **Dame** : 9 points
- **Roi** : ∞ (perte du roi = perte de la partie)

---

## ⚠️ Erreurs Courantes à Éviter

### 1. Jouer sans vérifier les échecs
❌ **Erreur :** Jouer un coup alors que votre roi est en échec
✅ **Solution :** TOUJOURS résoudre l'échec en priorité

### 2. Laisser le roi en échec
❌ **Erreur :** Jouer un coup qui met/laisse votre roi en échec
✅ **Solution :** Vérifier que le roi est en sécurité après chaque coup

### 3. Négliger le développement
❌ **Erreur :** Jouer le même pion 5 fois d'affilée
✅ **Solution :** Développer toutes vos pièces rapidement

### 4. Oublier de roquer
❌ **Erreur :** Laisser le roi au centre
✅ **Solution :** Roquer tôt (coups 5-10) pour mettre le roi en sécurité

### 5. Perdre des pièces gratuitement
❌ **Erreur :** Laisser une pièce non défendue
✅ **Solution :** Vérifier que toutes vos pièces sont protégées

---

## 📚 Glossaire des Termes

- **Échec** : Le roi est attaqué
- **Échec et Mat** : Le roi est attaqué et ne peut échapper
- **Pat** : Match nul (aucun coup légal mais pas en échec)
- **Roque** : Coup spécial roi + tour
- **En passant** : Prise spéciale de pion
- **Promotion** : Transformation du pion en 8ème rangée
- **Fourchette** : Attaque simultanée de 2+ pièces
- **Clouage** : Pièce qui ne peut bouger sans exposer le roi
- **Ouverture** : Les 10-15 premiers coups
- **Milieu de partie** : Phase tactique principale
- **Finale** : Phase avec peu de pièces restantes

---

## 🎮 Exemple de Partie Courte (Mat du Berger)

```
1. e4 e5     - Les deux joueurs contrôlent le centre
2. Bc4 Nc6   - Blanc développe le fou, Noir le cavalier
3. Qh5 Nf6?? - Blanc attaque f7, Noir ne voit pas le danger
4. Qxf7#     - ÉCHEC ET MAT !

Position finale :
♜ . ♝ ♛ ♚ ♝ . ♜
♟ ♟ ♟ ♟ . ♟ ♟ ♟
. . ♞ . . ♞ . .
. . . . ♟ ♕ . .  ← Dame blanche en f7 : MAT !
. . ♗ . ♙ . . .
. . . . . . . .
♙ ♙ ♙ ♙ . ♙ ♙ ♙
♖ ♘ ♗ . ♔ . . ♖

Le roi noir en e8 :
- Est en échec par la Dame en f7
- Ne peut aller en d8, d7, e7, f8 (contrôlés par la Dame)
- Aucune pièce ne peut capturer la Dame
- Aucune pièce ne peut bloquer
→ C'EST ÉCHEC ET MAT !
```

---

## 🏆 Résumé pour les Débutants

### Les 5 Règles d'Or

1. **Protégez votre roi** - C'est la pièce la plus importante
2. **Contrôlez le centre** - Les cases e4, d4, e5, d5 sont cruciales
3. **Développez vos pièces** - Sortez toutes vos pièces rapidement
4. **Roquez tôt** - Mettez votre roi en sécurité
5. **Réfléchissez avant de jouer** - Vérifiez qu'aucune pièce ne peut être capturée

### Pour Gagner

- Cherchez à mettre le roi adverse **en échec et mat**
- Capturez les pièces adverses (surtout la Dame)
- Protégez vos pièces importantes
- Utilisez tous vos coups pour créer des menaces

---

**Bon jeu ! ♔♕♖♗♘♙**

*Pour plus d'informations, consultez les règles officielles de la FIDE (Fédération Internationale des Échecs).*
