/**
 * EXEMPLE D'INTÉGRATION DES COMPOSANTS DE PERMISSIONS DYNAMIQUES
 * 
 * Ce fichier montre comment intégrer DynamicStats et DynamicActions
 * dans votre Dashboard pour un affichage 100% adapté aux permissions
 */

// Remplacer la section ACTIONS RAPIDES dans Dashboard.tsx par:

{/* ACTIONS RAPIDES - DYNAMIQUES SELON PERMISSIONS */}
<Box sx={{ mb: { xs: 2, sm: 3, md: 4 } }}>
  <Typography
    variant="h6"
    sx={{
      fontWeight: 800,
      color: '#003D66',
      mb: { xs: 1, sm: 1.5, md: 2 },
      fontSize: { xs: '0.8rem', sm: '0.95rem', md: '1.1rem' },
      textTransform: 'uppercase',
      letterSpacing: '0.3px',
    }}
  >
    📋 Actions Disponibles
  </Typography>
  <DynamicActions
    hasPermission={hasPermission}
    navigate={navigate}
    GovActionButton={GovActionButton}
    variant="full"
  />
</Box>

// ========================================

// Remplacer la section STATS dans DashboardContent par:

{/* STATISTIQUES - DYNAMIQUES SELON PERMISSIONS */}
<DynamicStats
  hasPermission={hasPermission}
  stats={stats}
  navigate={navigate}
  GovStatCard={GovStatCard}
  layout="full"
/>

// ========================================

// IMPORTS À AJOUTER EN HAUT DU FICHIER:

import { DynamicStats } from '../components/DynamicStats'
import { DynamicActions } from '../components/DynamicActions'
import { PermissionGate } from '../components/PermissionGate'

// ========================================

// EXEMPLE: Afficher une section Admin uniquement pour les ADMIN

<PermissionGate 
  hasPermission={hasPermission('view', 'manage_users')}
  hideOnDenied={true}
>
  <Box sx={{ mt: 4, p: 2, backgroundColor: '#f5f5f5', borderRadius: '8px' }}>
    <Typography variant="h6" sx={{ color: '#003D66', mb: 2 }}>
      🔐 Panel Administration
    </Typography>
    <Typography variant="body2" color="textSecondary">
      Contenu visible uniquement pour les administrateurs
    </Typography>
  </Box>
</PermissionGate>

// ========================================

// EXEMPLE: Filtrer les actions pour exclure certaines ressources

<DynamicActions
  hasPermission={hasPermission}
  navigate={navigate}
  GovActionButton={GovActionButton}
  variant="full"
  excludeResources={['users', 'reports']}  // Masquer ces ressources
/>

// ========================================

/**
 * RÉSULTAT PAR RÔLE
 * 
 * ADMIN:
 * - Voir: Tous les stats + Toutes les actions
 * - Actions: ➕ Trajet, ➕ Billet, ➕ Colis, ➕ Paiem., ➕ Emp., ➕ Villes, ➕ Rapport, ➕ User
 * 
 * COMPTABLE:
 * - Voir: Paiements, Chiffre d'Affaires, Employés
 * - Actions: ➕ Paiem., ➕ Rapport
 * 
 * GUICHETIER:
 * - Voir: Billets, Colis, Trajets
 * - Actions: ➕ Billet, ➕ Colis, ✏️ Trajets
 * 
 * CHAUFFEUR:
 * - Voir: Trajets, Billets
 * - Actions: ✏️ Trajets
 * 
 * CLIENT:
 * - Voir: Trajets, Billets, Colis
 * - Actions: Aucune (Lecture seule)
 */
