# 📊 Système de Permissions Dynamiques

Ce système permet d'afficher le contenu (statistiques, actions, données) en fonction des permissions de chaque utilisateur.

## 🎯 Composants Disponibles

### 1. **PermissionGate** - Contrôle d'accès simple
```tsx
import { PermissionGate } from '../components/PermissionGate'

<PermissionGate 
  hasPermission={hasPermission('view', 'payments')}
  hideOnDenied={true}
>
  <YourComponent />
</PermissionGate>
```

### 2. **DynamicStats** - Affichage des statistiques selon les permissions
```tsx
import { DynamicStats } from '../components/DynamicStats'

<DynamicStats
  hasPermission={hasPermission}
  stats={stats}
  navigate={navigate}
  GovStatCard={GovStatCard}
  layout="full"  // 'full' ou 'compact'
/>
```

### 3. **DynamicActions** - Affichage des actions selon les permissions
```tsx
import { DynamicActions } from '../components/DynamicActions'

<DynamicActions
  hasPermission={hasPermission}
  navigate={navigate}
  GovActionButton={GovActionButton}
  variant="full"  // 'full' ou 'compact'
  excludeResources={['users', 'settings']}  // Optionnel
/>
```

## 📋 Tableau des Permissions par Rôle

### ADMIN (Administrateur)
- ✅ Tous les accès CRUD (Create, Read, Update, Delete)
- ✅ Peut gérer les utilisateurs
- ✅ Accès aux paramètres

### COMPTABLE (Comptable)
- ✅ Voir: Paiements, Revenus, Rapports, Employés
- ✅ Créer/Éditer: Paiements, Rapports
- ❌ Supprimer: Aucune ressource

### GUICHETIER (Guichetier)
- ✅ Voir: Billets, Colis, Trajets
- ✅ Créer/Éditer: Billets, Colis
- ❌ Voir/Modifier: Paiements, Employés, Villes

### CHAUFFEUR (Chauffeur)
- ✅ Voir: Trajets, Billets
- ✅ Éditer: Trajets
- ❌ Créer: Aucune ressource

### CONTROLEUR (Contrôleur)
- ✅ Voir: Billets, Trajets, Employés
- ✅ Éditer: Billets, Trajets
- ❌ Créer/Supprimer: Aucune ressource

### GESTIONNAIRE_COURRIER (Gestionnaire de Courrier)
- ✅ Voir: Colis, Villes
- ✅ Créer/Éditer: Colis
- ❌ Voir/Modifier: Paiements, Trajets

### CLIENT (Client)
- ✅ Voir: Trajets, Billets, Colis
- ❌ Créer/Éditer/Supprimer: Toutes les ressources

## 🔧 Exemple d'Intégration Complète

```tsx
import React from 'react'
import { DynamicStats } from '../components/DynamicStats'
import { DynamicActions } from '../components/DynamicActions'
import { PermissionGate } from '../components/PermissionGate'

export const MyDashboard: React.FC = () => {
  const { hasPermission, stats, navigate, GovStatCard, GovActionButton } = useDashboard()

  return (
    <Box>
      {/* Afficher les stats accessibles */}
      <DynamicStats
        hasPermission={hasPermission}
        stats={stats}
        navigate={navigate}
        GovStatCard={GovStatCard}
        layout="full"
      />

      {/* Afficher les actions accessibles */}
      <DynamicActions
        hasPermission={hasPermission}
        navigate={navigate}
        GovActionButton={GovActionButton}
        excludeResources={['users']}
      />

      {/* Contenu conditionnel basé sur une permission spécifique */}
      <PermissionGate 
        hasPermission={hasPermission('edit', 'reports')}
      >
        <Box>
          <Typography variant="h6">Panel d'Administration des Rapports</Typography>
          {/* Contenu réservé aux éditeurs de rapports */}
        </Box>
      </PermissionGate>
    </Box>
  )
}
```

## 🎨 Personnalisation

### Ajouter une nouvelle ressource

1. Ajouter dans `AVAILABLE_ACTIONS` (DynamicActions.tsx):
```tsx
{
  resource: 'myresource',
  label: 'Ma Ressource',
  icon: MyIcon,
  path: '/myresource',
  createPath: '/myresource?action=create',
  color: '#FF5722',
},
```

2. Ajouter dans `ROLE_PERMISSIONS` (Dashboard.tsx):
```tsx
ADMIN: {
  view: [..., 'myresource'],
  create: [..., 'myresource'],
  edit: [..., 'myresource'],
  delete: [..., 'myresource'],
},
```

3. Ajouter dans les stats si applicable (DynamicStats.tsx):
```tsx
{
  resource: 'myresource',
  title: 'Ma Ressource',
  value: stats.myresource || 0,
  icon: MyIcon,
  color: '#FF5722',
  path: '/myresource',
},
```

## 🚀 Mise en Œuvre

```bash
# 1. Créer les utilisateurs avec permissions
cd /home/lidruf/TRANSPORT/backend
python manage.py shell < create_all_users.py

# 2. Intégrer dans Dashboard.tsx
# Remplacer le code des actions par:
<DynamicActions
  hasPermission={hasPermission}
  navigate={navigate}
  GovActionButton={GovActionButton}
/>

# 3. Intégrer dans les pages (CitiesPage, PaymentsPage, etc.)
# Ajouter au début:
<PermissionGate 
  hasPermission={hasPermission('view', 'cities')}
  hideOnDenied={true}
>
  {/* Contenu de la page */}
</PermissionGate>
```

## 📊 Résumé des Permissions par Ressource

| Ressource | View | Create | Edit | Delete |
|-----------|------|--------|------|--------|
| trips | ADMIN, CHAUFFEUR, CONTROLEUR, GUICHETIER | ADMIN, GUICHETIER | ADMIN, CHAUFFEUR, CONTROLEUR, GUICHETIER | ADMIN |
| tickets | ADMIN, CHAUFFEUR, CONTROLEUR, GUICHETIER, CLIENT | ADMIN, GUICHETIER | ADMIN, CHAUFFEUR, CONTROLEUR, GUICHETIER | ADMIN |
| parcels | ADMIN, GUICHETIER, GESTIONNAIRE_COURRIER, CLIENT | ADMIN, GUICHETIER, GESTIONNAIRE_COURRIER | ADMIN, GUICHETIER, GESTIONNAIRE_COURRIER | ADMIN |
| payments | ADMIN, COMPTABLE | ADMIN, COMPTABLE | ADMIN, COMPTABLE | ADMIN |
| revenue | ADMIN, COMPTABLE | - | - | - |
| reports | ADMIN, COMPTABLE | ADMIN, COMPTABLE | ADMIN, COMPTABLE | ADMIN |
| employees | ADMIN, COMPTABLE, CONTROLEUR | ADMIN | ADMIN | ADMIN |
| cities | ADMIN, GESTIONNAIRE_COURRIER | ADMIN | ADMIN | ADMIN |
| users | ADMIN | ADMIN | ADMIN | ADMIN |

## 💡 Bonnes Pratiques

1. **Toujours vérifier les permissions côté backend** - Ne vous fiez pas seulement au frontend
2. **Utiliser PermissionGate pour les sections sensibles** - Masquer les formulaires sensibles
3. **Préférer DynamicStats et DynamicActions** - Plutôt que des conditions manuelles
4. **Tester avec chaque rôle** - Vérifier que l'accès est correct pour chaque utilisateur
5. **Documenter les nouvelles permissions** - Garder ce fichier à jour

## 🔗 Fichiers Relatifs

- `/frontend/src/components/PermissionGate.tsx` - Contrôle d'accès
- `/frontend/src/components/DynamicActions.tsx` - Actions dynamiques
- `/frontend/src/components/DynamicStats.tsx` - Statistiques dynamiques
- `/frontend/src/pages/Dashboard.tsx` - Implémentation dans le dashboard
- `/backend/create_all_users.py` - Script de création d'utilisateurs
