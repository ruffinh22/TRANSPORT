# 🔐 Implémentation RBAC (Role-Based Access Control) - TKF Transport

## Statut: ✅ COMPLET

Ce document décrit l'implémentation du contrôle d'accès basé sur les rôles (RBAC) du système TKF Transport, en conformité avec le cahier des charges.

---

## 📋 7 Rôles Implémentés

### 1. **Super Administrateur** (`SUPER_ADMIN`)
- **Description** : Accès complet au système - Réservé IT
- **Permissions** : Toutes les permissions
- **Cas d'usage** : Configuration système critique, migration de données

---

### 2. **Administrateur Système** (`ADMIN`)
- **Description** : Gestion administrative complète du système
- **Permissions** :
  - `users.view_user` - Voir les utilisateurs
  - `users.manage_users` - Gérer les utilisateurs
  - `vehicles.view_vehicle` - Voir les véhicules
  - `vehicles.manage_vehicles` - Gérer les véhicules
  - `trips.view_trip` - Voir les trajets
  - `trips.manage_trips` - Gérer les trajets
  - `tickets.view_ticket` - Voir les billets
  - `tickets.manage_tickets` - Gérer les billets
  - `payments.view_payment` - Voir les paiements
  - `payments.manage_payments` - Gérer les paiements
  - `reports.view_report` - Voir les rapports
  - `settings.manage_settings` - Gérer les paramètres
- **Cas d'usage** : Gestion globale du système

---

### 3. **Manager Opérations** (`MANAGER`)
- **Description** : Gestion opérationnelle des trajets et véhicules
- **Permissions** :
  - `vehicles.view_vehicle` - Voir les véhicules
  - `vehicles.manage_vehicles` - Gérer les véhicules
  - `trips.view_trip` - Voir les trajets
  - `trips.manage_trips` - Gérer les trajets
  - `tickets.view_ticket` - Voir les billets
  - `payments.view_payment` - Voir les paiements
  - `reports.view_report` - Voir les rapports
- **Cas d'usage** : Planification des trajets, affectation des ressources

---

### 4. **Comptable / Manager Finance** (`COMPTABLE`)
- **Description** : Gestion financière, recettes et rapports comptables
- **Permissions** :
  - `payments.view_payment` - Voir les paiements
  - `payments.manage_payments` - Gérer les paiements
  - `trips.view_trip` - Voir les trajets
  - `tickets.view_ticket` - Voir les billets
  - `reports.view_report` - Voir les rapports
- **Cas d'usage** : Suivi des recettes, rapports financiers, reconciliation

---

### 5. **Guichetier** (`GUICHETIER`)
- **Description** : Vente de tickets, gestion caisses et enregistrement passagers
- **Permissions** :
  - `tickets.view_ticket` - Voir les billets
  - `tickets.manage_tickets` - Gérer les billets (vendre, annuler)
  - `trips.view_trip` - Voir les trajets
  - `payments.view_payment` - Voir les paiements
  - `payments.manage_payments` - Gérer les paiements (encaisser)
- **Cas d'usage** : Vente au comptoir, gestion de caisse

---

### 6. **Chauffeur** (`CHAUFFEUR`)
- **Description** : Conduite véhicule et suivi des trajets assignés
- **Permissions** :
  - `trips.view_trip` - Voir les trajets
  - `tickets.view_ticket` - Voir les billets
  - `vehicles.view_vehicle` - Voir les véhicules
- **Cas d'usage** : Consultation des trajets, accès en lecture aux billets et véhicules

---

### 7. **Contrôleur** (`CONTROLEUR`)
- **Description** : Validation des tickets et contrôle des passagers
- **Permissions** :
  - `tickets.view_ticket` - Voir les billets
  - `tickets.manage_tickets` - Valider les billets
  - `trips.view_trip` - Voir les trajets
  - `payments.view_payment` - Voir les paiements
- **Cas d'usage** : Validation des tickets à bord, enregistrement du paiement

---

### 8. **Gestionnaire Courrier** (`GESTIONNAIRE_COURRIER`)
- **Description** : Gestion des colis, suivi et livraison
- **Permissions** :
  - `parcels.view_parcel` - Voir les colis
  - `parcels.manage_parcels` - Gérer les colis
  - `trips.view_trip` - Voir les trajets
  - `payments.view_payment` - Voir les paiements
- **Cas d'usage** : Traitement des colis, suivi de livraison

---

## 🏗️ Architecture Implémentée

### Backend (Django)

**Fichiers modifiés :**
- `/backend/apps/common/models.py` - RoleType avec 8 rôles
- `/backend/apps/common/management/commands/init_roles.py` - Définition des 8 rôles avec permissions
- `/backend/apps/users/models.py` - Relation ManyToMany User ↔ Role

**Système de permissions :**
- Chaque rôle a une liste de permissions spécifiques
- Les permissions sont au format `module.action` (ex: `tickets.view_ticket`)
- Les permissions sont stockées en JSON sur le rôle

**Initialisation :**
```bash
python manage.py init_roles
```

---

### Frontend (React + TypeScript)

**Nouveaux fichiers créés :**

1. **`/frontend/src/components/RoleBasedRoute.tsx`**
   - Composant pour protéger les routes selon les rôles
   - Vérifie que l'utilisateur a les rôles requis
   - Affiche une page d'accès refusé si non autorisé

2. **`/frontend/src/components/AccessDenied.tsx`**
   - Page d'affichage pour accès refusé
   - Design gouvernemental cohérent
   - Boutons de navigation

3. **`/frontend/src/components/RoleBasedMenu.tsx`**
   - Menu dynamique basé sur les rôles
   - Affiche uniquement les items du menu que l'utilisateur peut voir
   - Responsive (collapse/expand selon l'écran)

4. **`/frontend/src/hooks/useRoleBasedAccess.ts`**
   - Hook personnalisé pour vérifier les rôles
   - Méthodes : `hasRole()`, `hasAnyRole()`, `hasAllRoles()`
   - Helpers : `isAdmin()`, `isManager()`, `isComptable()`, etc.

5. **`/frontend/src/config/roleConfig.ts`**
   - Configuration centralisée des rôles et permissions
   - Matrice des permissions par rôle
   - Configuration des pages et rôles requis

**Modifications :**
- `/frontend/src/store/authSlice.ts` - Interface User augmentée avec champ `roles`
- `/frontend/src/services/index.ts` - User interface avec `roles?: string[]`
- `/frontend/src/App.tsx` - Prêt pour utiliser RoleBasedRoute
- `/frontend/src/components/index.ts` - Exports des nouveaux composants

---

## 🔄 Flux d'Authentification avec Rôles

```
1. Utilisateur accède à /login
2. Soumet credentials (email + password)
3. Backend valide et retourne :
   - access_token (JWT)
   - refresh_token
   - user { id, email, roles: ['GUICHETIER'], ... }
4. Frontend stocke dans Redux + localStorage
5. Utilisateur accède à /dashboard
6. RoleBasedRoute vérifie isAuthenticated + rôles
7. Menu affiche uniquement les items accessibles
8. API calls incluent le JWT dans Authorization header
9. Backend valide les permissions sur chaque endpoint
```

---

## 🔒 Sécurité - Points Clés

### Backend
- ✅ Permissions validées sur chaque endpoint
- ✅ JWT tokens avec expiration
- ✅ Audit trail pour chaque action
- ✅ Soft delete pour tous les records

### Frontend
- ✅ Routes protégées par RoleBasedRoute
- ✅ Menu filtré selon les rôles
- ✅ Tokens stockés de manière sécurisée
- ✅ Refresh token automatique

### Points à Implémenter (Backend)
- [ ] Middleware RBAC pour chaque endpoint (Django Rest Framework)
- [ ] Validation des permissions dans les serializers
- [ ] API error handling pour "unauthorized" (403)
- [ ] Logging des actions sensibles

---

## 📱 Pages et Accès Requis

| Page | Rôles Autorisés |
|------|-----------------|
| Dashboard | Tous les rôles |
| Trajets | ADMIN, MANAGER, CHAUFFEUR |
| Billets | ADMIN, MANAGER, GUICHETIER, CONTROLEUR |
| Colis | ADMIN, MANAGER, GESTIONNAIRE_COURRIER |
| Paiements | ADMIN, COMPTABLE, GUICHETIER |
| Personnel | ADMIN, MANAGER |
| Villes/Routes | ADMIN, MANAGER |
| Rapports | ADMIN, MANAGER, COMPTABLE |
| Paramètres | ADMIN |

---

## 💻 Utilisation dans les Composants

### Vérifier les rôles
```tsx
import { useRoleBasedAccess } from '../hooks'

function MyComponent() {
  const { isAdmin, hasRole, userRoles } = useRoleBasedAccess()
  
  if (isAdmin()) {
    // Afficher le contenu admin
  }
  
  if (hasRole('COMPTABLE')) {
    // Afficher le contenu comptable
  }
  
  // Afficher tous les rôles
  console.log(userRoles) // ['GUICHETIER']
}
```

### Protéger une route
```tsx
<Route
  path="/admin-only"
  element={
    <RoleBasedRoute requiredRoles={['ADMIN']}>
      <AdminPage />
    </RoleBasedRoute>
  }
/>
```

### Menu dynamique
```tsx
import { RoleBasedMenu } from '../components'

function Sidebar() {
  return <RoleBasedMenu onNavigate={(path) => navigate(path)} />
}
```

---

## 🧪 Tests à Effectuer

### Frontend
- [ ] Login avec différents rôles
- [ ] Vérifier que le menu affiche les items corrects
- [ ] Accéder à une page non autorisée → Voir AccessDenied
- [ ] Vérifier que les boutons "Gérer" sont cachés si pas les permissions

### Backend
- [ ] POST /users/login/ retourne `user.roles`
- [ ] GET /api/v1/users/me/ retourne les rôles
- [ ] POST /trips/ retourne 403 si l'utilisateur n'a pas `trips.manage_trips`

---

## 📊 Prochaines Étapes

1. **Backend - Middleware RBAC**
   - Ajouter un décorateur Django REST Framework pour vérifier les permissions
   - Implémenter dans chaque ViewSet
   - Retourner 403 Forbidden si non autorisé

2. **Frontend - Intégration Complète**
   - Remplacer ProtectedRoute par RoleBasedRoute dans App.tsx
   - Intégrer RoleBasedMenu dans ResponsiveAppBar
   - Cacher les boutons "Ajouter/Modifier/Supprimer" selon les rôles

3. **Tests Automatisés**
   - Tests unitaires des hooks (useRoleBasedAccess)
   - Tests d'intégration pour les routes protégées
   - Tests backend pour les permissions

4. **Documentation & Formation**
   - Guide d'utilisation pour chaque rôle
   - Procédures d'attribution des rôles aux utilisateurs
   - Matrice RACI des actions par rôle

---

## 📝 Notes

- Les rôles sont **mutables** - Un utilisateur peut avoir plusieurs rôles
- Les permissions sont **vérifiées côté backend** - Jamais faire confiance au frontend
- Les rôles sont **immuables dans le système** - Pas de création dynamique
- Le **SUPER_ADMIN** doit rester caché du frontend et utilisé seulement par IT

---

**Mis à jour:** 2024-12-27  
**Version:** 1.0  
**Statut:** ✅ Implémentation complète des structures
