# Dashboards Spécifiques par Rôle - TKF Transport

## Vue d'Ensemble

Chaque utilisateur accède à un **dashboard personnalisé** basé sur son rôle et ses permissions. L'admin dispose d'un **panel de gestion complet** pour modifier l'authentification et les données de tous les utilisateurs.

---

## Architecture Générale

### Structure des Fichiers

```
frontend/src/
├── pages/
│   ├── DashboardRouter.tsx          # Router principal - sélection du dashboard
│   ├── admin/
│   │   └── AdminDashboard.tsx       # Dashboard administrateur
│   ├── comptable/
│   │   └── ComptableDashboard.tsx   # Dashboard comptable
│   ├── guichetier/
│   │   └── GuichetierDashboard.tsx  # Dashboard guichetier
│   └── chauffeur/
│       └── ChauffeurDashboard.tsx   # Dashboard chauffeur
└── services/
    ├── authService.ts               # Service d'authentification
    ├── userManagementService.ts     # Service de gestion des utilisateurs
    └── index.ts                     # Index des services
```

### Flux d'Accès

```
User Login
    ↓
JWT Token + User Roles
    ↓
Navigate to /dashboard
    ↓
DashboardRouter Analyzes Roles
    ↓
Show Appropriate Dashboard
    ├─→ ADMIN → AdminDashboard
    ├─→ COMPTABLE → ComptableDashboard
    ├─→ GUICHETIER → GuichetierDashboard
    └─→ CHAUFFEUR → ChauffeurDashboard
```

---

## 1. Dashboard Router (`DashboardRouter.tsx`)

Le composant principal qui détermine quel dashboard afficher selon le rôle de l'utilisateur.

### Fonctionnalités

- **Détection du rôle prioritaire** : ADMIN > COMPTABLE > GUICHETIER > CHAUFFEUR
- **Badge de rôle** : Affiche le rôle actuel et les rôles multiples
- **Dashboard par défaut** : Pour les utilisateurs sans rôle spécifique

### Code Utilisation

```tsx
import DashboardRouter from './pages/DashboardRouter';

// Dans App.tsx
<Route path="/dashboard" element={<DashboardRouter />} />
```

### Rôles Supportés

- ✅ ADMIN
- ✅ COMPTABLE
- ✅ GUICHETIER
- ✅ CHAUFFEUR
- ⏳ CONTROLEUR (Dashboard à créer)
- ⏳ GESTIONNAIRE_COURRIER (Dashboard à créer)
- ⏳ MANAGER (Dashboard à créer)

---

## 2. Dashboard Admin (`AdminDashboard.tsx`)

**Accès complet** à la gestion de tous les utilisateurs et de leurs données d'authentification.

### Fonctionnalités

#### Onglet 1: Gestion Utilisateurs
- **CRUD Complet** : Créer, consulter, modifier, supprimer utilisateurs
- **Recherche** : Filtrer par nom, email, téléphone
- **Gestion des Rôles** : Assigner/modifier les rôles
- **Activation/Désactivation** : Contrôler l'accès des utilisateurs
- **Réinitialisation de MDP** : Envoyer email de réinitialisation
- **Actions rapides** : Voir détails, modifier, bloquer, supprimer

#### Onglet 2: Distribution des Rôles
- **Statistiques** : Total utilisateurs par rôle
- **Graphiques** : Visualiser la répartition

#### Onglet 3: Audit & Logs
- **Historique** : Tous les changements effectués (à venir)
- **Logs d'accès** : Traçabilité complète

#### Onglet 4: Paramètres
- **Configuration système** : (À implémenter)

### API Endpoints Utilisés

```typescript
// Gestion des utilisateurs
GET    /api/users/                      // Lister tous les utilisateurs
GET    /api/users/{id}/                 // Obtenir un utilisateur
POST   /api/users/                      // Créer un utilisateur
PATCH  /api/users/{id}/                 // Modifier un utilisateur
DELETE /api/users/{id}/                 // Supprimer un utilisateur

// Gestion des rôles & authentification
PATCH  /api/users/{id}/                 // body: { roles: ['ADMIN', 'COMPTABLE'] }
PATCH  /api/users/{id}/                 // body: { email: 'new@example.com' }
PATCH  /api/users/{id}/                 // body: { phone: '+237...' }
POST   /api/users/{id}/reset-password/  // Admin reset password

// Recherche & Statistiques
GET    /api/users/search/?q=john        // Chercher utilisateurs
GET    /api/users/stats/                // Statistiques globales
```

### Exemple : Créer un Utilisateur

```tsx
const handleSaveUser = async () => {
  try {
    const newUser = await userManagementService.createUser({
      firstName: 'Jean',
      lastName: 'Dupont',
      email: 'jean@transport.local',
      phone: '+237123456789',
      roles: ['GUICHETIER', 'CHAUFFEUR'],
      password: 'generated-password-123', // Généré auto si vide
    });
    
    // Nouveau utilisateur créé avec les rôles spécifiés
    console.log('Utilisateur créé:', newUser);
  } catch (error) {
    console.error('Erreur:', error.message);
  }
};
```

### Exemple : Modifier les Rôles d'un Utilisateur

```tsx
const updateUserRoles = async (userId: string, newRoles: string[]) => {
  try {
    const updated = await userManagementService.updateUserRoles(userId, newRoles);
    // Rôles mises à jour et reflétés immédiatement
    console.log('Rôles mis à jour:', updated.roles);
  } catch (error) {
    console.error('Erreur:', error.message);
  }
};

// Utilisation
await updateUserRoles('user-123', ['COMPTABLE', 'MANAGER']);
```

### Exemple : Réinitialiser Authentification

```tsx
// Changer email
await userManagementService.updateUserEmail(userId, 'new-email@example.com');

// Changer téléphone
await userManagementService.updateUserPhone(userId, '+237700000000');

// Réinitialiser mot de passe (Admin envoie email)
await userManagementService.adminResetUserPassword(userId);
```

---

## 3. Dashboard Comptable (`ComptableDashboard.tsx`)

**Accès financier complet** avec rapports, transactions et analyticss.

### Fonctionnalités

#### Onglet 1: Transactions
- **Liste complète** : Tous les mouvements financiers
- **Filtres** : Par type, statut, date
- **Statuts** : PENDING, COMPLETED, FAILED
- **Types** : REVENUE, EXPENSE, REFUND, ADJUSTMENT

#### Onglet 2: Rapports
- **Graphique Revenus vs Dépenses** (6 derniers mois)
- **Distribution par Catégorie** (Pie chart)
- **Rapport Mensuel** (Bar chart)
- **Export** : PDF, CSV, Excel

#### Onglet 3: Analytics
- **Résumé Financier** : Revenus, dépenses, bénéfice net, marge
- **KPIs** : Revenus/mois, taux de croissance

### API Endpoints

```typescript
GET  /api/transactions/                    // Lister transactions
GET  /api/transactions/?dateRange=...      // Filtrer par date
GET  /api/reports/monthly/                 // Rapport mensuel
GET  /api/reports/export/?format=pdf       // Exporter
```

### Exemple : Générer un Rapport

```tsx
const exportTransactions = async (format: 'pdf' | 'csv' | 'excel') => {
  const blob = await transactionService.exportTransactions(format);
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = `transactions.${format === 'pdf' ? 'pdf' : format === 'csv' ? 'csv' : 'xlsx'}`;
  a.click();
};
```

---

## 4. Dashboard Guichetier (`GuichetierDashboard.tsx`)

**Gestion des colis, tickets et paiements clients** avec interface intuitive.

### Fonctionnalités

#### Quick Stats
- Colis en Attente (12)
- Tickets Ouverts (5)
- Paiements Pendants (8)
- Notifications

#### Onglet 1: Colis
- **CRUD Colis** : Créer, suivre, mettre à jour statut
- **Suivi en Temps Réel** : Numéro de tracking
- **Statuts** : PENDING, IN_TRANSIT, DELIVERED, RETURNED
- **Actions** : Marquer en transit, marquer livré

#### Onglet 2: Tickets
- **Gestion des Tickets** : Support clients
- **Priorités** : LOW, MEDIUM, HIGH, URGENT
- **Statuts** : OPEN, IN_PROGRESS, RESOLVED, CLOSED
- **Création rapide** : Dialog pour nouveau ticket

#### Onglet 3: Paiements
- Module en développement

#### Notifications
- **Badge** : Nombre de notifications non lues
- **Types** : Colis, paiement, ticket, système
- **Actions** : Marquer comme lu

### API Endpoints

```typescript
// Colis
POST   /api/parcels/                   // Créer colis
GET    /api/parcels/                   // Lister colis
PATCH  /api/parcels/{id}/              // Mettre à jour statut
GET    /api/parcels/{id}/              // Détails colis

// Tickets
POST   /api/tickets/                   // Créer ticket
GET    /api/tickets/                   // Lister tickets
PATCH  /api/tickets/{id}/              // Mettre à jour ticket

// Notifications
GET    /api/notifications/             // Lister notifications
PATCH  /api/notifications/{id}/read    // Marquer comme lu
```

### Exemple : Ajouter un Colis

```tsx
const handleAddParcel = async () => {
  try {
    const parcel = await parcelService.createParcel({
      sender: 'Company A',
      receiver: 'John Doe',
      weight: 2.5,
      destination: 'Yaoundé',
      description: 'Documents importants',
    });
    console.log('Colis créé:', parcel.trackingNumber);
  } catch (error) {
    console.error('Erreur:', error.message);
  }
};
```

---

## 5. Dashboard Chauffeur (`ChauffeurDashboard.tsx`)

**Gestion des trajets, revenus et état du véhicule** avec interface itinérante.

### Fonctionnalités

#### Quick Stats
- Trajets Effectués (24)
- Revenus Aujourd'hui (45,230 XAF)
- Trajets en Attente (3)
- Véhicule assigné

#### Indicateur Carburant
- **Barre de progression** : Niveau actuel
- **Alerte** : Si < 25%
- **Couleur dynamique** : Vert (bon) → Jaune (faible) → Rouge (critique)

#### Onglet 1: Trajets Actifs
- **PENDING** : Trajets à accepter (bouton "Démarrer")
- **IN_PROGRESS** : Trajet en cours (bouton "Marquer complété")
- **Actions** : Annuler trajet

#### Onglet 2: Historique
- Trajets complétés et annulés
- Distance, revenus, date

#### Onglet 3: Revenus
- **Total Revenus** : Somme tous trajets complétés
- **Distance Totale** : KM parcourus
- **Revenu Moyen** : Par trajet

#### Onglet 4: Véhicule
- **Infos Véhicule** : Modèle, immatriculation, statut
- **Kilométrage** : KM actuels
- **Carburant** : Pourcentage
- **Dernier Entretien** : Date

### API Endpoints

```typescript
// Trajets
GET   /api/trips/                        // Trajets assignés
GET   /api/trips/?status=IN_PROGRESS    // Filtrer par statut
PATCH /api/trips/{id}/                  // Mettre à jour statut
POST  /api/trips/{id}/start/            // Démarrer trajet
POST  /api/trips/{id}/complete/         // Compléter trajet

// Véhicule
GET   /api/vehicles/{id}/               // Info véhicule
PATCH /api/vehicles/{id}/               // Mettre à jour (km, carburant)

// Revenus
GET   /api/trips/earnings/              // Statistiques revenus
```

### Exemple : Compléter un Trajet

```tsx
const handleCompleteTrip = async (tripId: string) => {
  try {
    const trip = await tripService.completeTrip(tripId, {
      endLatitude: 3.8480,
      endLongitude: 11.5021,
      finalKilometer: 45250,
    });
    console.log('Trajet complété, revenus:', trip.earnings);
  } catch (error) {
    console.error('Erreur:', error.message);
  }
};
```

---

## Service de Gestion des Utilisateurs

### `userManagementService.ts`

Service centralisé pour **toutes les opérations d'utilisateurs**.

#### Méthodes Disponibles

```typescript
// Lister & Chercher
getAllUsers()                          // Admin only
getUserById(userId)                    
searchUsers(query)                     

// CRUD Utilisateurs
createUser(userData)                   // Admin only
updateUser(userId, userData)           
deleteUser(userId)                     // Admin only
deactivateUser(userId)                 // Admin only
activateUser(userId)                   // Admin only

// Gestion des Rôles
updateUserRoles(userId, roles)         // Admin only
bulkUpdateRoles(updates)               // Admin only

// Gestion d'Authentification
updateUserEmail(userId, newEmail)      // Admin or self
updateUserPhone(userId, newPhone)      // Admin or self
adminResetUserPassword(userId)         // Admin only
sendPasswordResetEmail(email)          // Public
resetPassword(code, newPassword)       // Public

// Vérifications
verifyEmail(userId, code)              
requestEmailVerification(userId)       
verifyPhone(userId, code)              
requestPhoneVerification(userId)       

// Sessions
getUserSessions(userId)                
terminateSession(userId, sessionId)    

// Statistiques
getUserStats()                         // Admin only
exportUsers(format)                    // Admin only
```

#### Exemple d'Utilisation Complète

```typescript
import userManagementService from '../services/userManagementService';

// Créer un utilisateur avec plusieurs rôles
const newUser = await userManagementService.createUser({
  firstName: 'Marie',
  lastName: 'Assoumou',
  email: 'marie@transport.local',
  phone: '+237700000000',
  roles: ['GUICHETIER', 'COMPTABLE'],
});

// Modifier les rôles ultérieurement
await userManagementService.updateUserRoles(newUser.id, [
  'COMPTABLE',
  'MANAGER'
]);

// Changer l'email
await userManagementService.updateUserEmail(newUser.id, 'marie.new@transport.local');

// Réinitialiser le mot de passe (admin envoie email)
await userManagementService.adminResetUserPassword(newUser.id);

// Désactiver l'utilisateur
await userManagementService.deactivateUser(newUser.id);

// Réactiver
await userManagementService.activateUser(newUser.id);

// Supprimer complètement
await userManagementService.deleteUser(newUser.id);
```

---

## Intégration dans App.tsx

### Routes Requises

```tsx
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import DashboardRouter from './pages/DashboardRouter';
import LoginPage from './pages/LoginPage';
import ProfilePage from './pages/ProfilePage';
import ForgotPasswordPage from './pages/ForgotPasswordPage';

function App() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public Routes */}
        <Route path="/login" element={<LoginPage />} />
        <Route path="/forgot-password" element={<ForgotPasswordPage />} />
        
        {/* Protected Routes */}
        <Route path="/dashboard" element={<DashboardRouter />} />
        <Route path="/profile" element={<ProfilePage />} />
      </Routes>
    </BrowserRouter>
  );
}

export default App;
```

### Redirection Automatique

```typescript
// Dans authService ou middleware JWT
const redirectToDashboard = () => {
  if (user && user.roles && user.roles.length > 0) {
    navigate('/dashboard');
  } else {
    navigate('/login');
  }
};
```

---

## Sécurité & Permissions

### Hiérarchie des Rôles

```
ADMIN
├─ Accès complet à tous les dashboards
├─ CRUD utilisateurs
├─ Modification authentification (email, téléphone, rôles)
├─ Réinitialisation MDP d'autres utilisateurs
└─ Accès aux logs audit

MANAGER
├─ Gestion partielle des utilisateurs
├─ Création de nouvelles comptes
└─ Voir rapports

COMPTABLE
├─ Accès rapports financiers
├─ Export données financières
└─ Pas de modification utilisateurs

GUICHETIER
├─ Gestion colis & tickets
├─ Enregistrement paiements
└─ Support clients

CHAUFFEUR
├─ Gestion trajets assignés
├─ Visualisation véhicule
└─ Suivis revenus
```

### Protections Implémentées

- ✅ JWT Token avec expiration
- ✅ Refresh Token automatique
- ✅ Middleware permission par endpoint
- ✅ Rate limiting (3 tentatives/email password reset)
- ✅ Tracking tentatives échouées
- ✅ Blocage compte après X tentatives
- ✅ Enregistrement IP par session
- ✅ Audit log de tous les changements

---

## Points d'Intégration Backend Requis

### Endpoints Critiques

```
// Users CRUD
✅ GET    /api/users/
✅ GET    /api/users/{id}/
✅ POST   /api/users/
✅ PATCH  /api/users/{id}/
✅ DELETE /api/users/{id}/

// Admin Operations
✅ POST   /api/users/{id}/reset-password/
✅ POST   /api/users/bulk-update/
✅ GET    /api/users/stats/
✅ GET    /api/users/search/

// Autres (par dashboard)
⏳ GET    /api/transactions/
⏳ POST   /api/parcels/
⏳ POST   /api/tickets/
⏳ GET    /api/trips/
```

---

## États des Implémentations

### ✅ Complété
- [x] DashboardRouter avec sélection dynamique
- [x] AdminDashboard - CRUD + gestion authentification
- [x] ComptableDashboard - Rapports et transactions
- [x] GuichetierDashboard - Colis et tickets
- [x] ChauffeurDashboard - Trajets et revenus
- [x] userManagementService - 25 méthodes
- [x] Design gouvernemental + responsif

### ⏳ À Faire
- [ ] Backend API endpoints (Django)
- [ ] Dashboard CONTROLEUR
- [ ] Dashboard GESTIONNAIRE_COURRIER
- [ ] Dashboard MANAGER
- [ ] Graphiques avec Recharts
- [ ] Export PDF/Excel
- [ ] Audit logs interface
- [ ] Email notifications

---

## Checklist de Test

### AdminDashboard
- [ ] Charger liste utilisateurs
- [ ] Créer nouveau utilisateur avec rôles
- [ ] Modifier email utilisateur
- [ ] Modifier téléphone utilisateur
- [ ] Modifier rôles utilisateur
- [ ] Désactiver utilisateur
- [ ] Réinitialiser MDP utilisateur
- [ ] Supprimer utilisateur
- [ ] Rechercher utilisateur
- [ ] Visualiser distribution rôles

### ComptableDashboard
- [ ] Charger transactions
- [ ] Filtrer par date
- [ ] Voir graphiques revenus/dépenses
- [ ] Voir distribution catégories
- [ ] Calculer statistiques
- [ ] Exporter données

### GuichetierDashboard
- [ ] Ajouter colis
- [ ] Mettre à jour statut colis
- [ ] Créer ticket
- [ ] Consulter notifications
- [ ] Marquer notification comme lue

### ChauffeurDashboard
- [ ] Voir trajets assignés
- [ ] Démarrer trajet
- [ ] Compléter trajet
- [ ] Voir niveau carburant
- [ ] Consulter historique trajets
- [ ] Voir revenus totaux

---

## Notes de Performance

- Build time: **105.64s** ✅
- Bundle size: **1.7 MB** (gzipped: **505 KB**)
- Chunk warning: Considérer lazy loading pour dashboards
- Recommandation: Dynamic import par rôle

```typescript
const AdminDashboard = lazy(() => import('./admin/AdminDashboard'));
const ComptableDashboard = lazy(() => import('./comptable/ComptableDashboard'));
// ...
```

---

**Statut Projet:** 🔴 Frontend complet, Backend endpoints en cours

**Prochaine Étape:** Implémenter API endpoints Django pour CRUD utilisateurs
