#!/bin/bash

# Script: Upgrade All Pages to Government Design Standard
# This script will create enhanced versions of all pages with government styling

cd /home/lidruf/TRANSPORT

echo "🏛️ Upgrading All Pages to Professional Government Design..."
echo ""

# Create a summary file
cat > PAGES_UPGRADE_PLAN.md << 'EOF'
# 🏛️ Plan de Mise à Jour des Pages au Design Gouvernemental

## Pages à Mettre à Jour (7 pages principales)

### 1. ✅ Dashboard.tsx
**Status**: FAIT - Design gouvernemental complet
- Couleurs officielles (Bleu #003D66, Rouge #CE1126, Vert #007A5E, Or #FFD700)
- Cartes statistiques cliquables avec borders codifiées
- Boutons actions gouvernementaux
- Responsive mobile/tablet/desktop
- En-tête professionnel avec infos utilisateur
- Pied de page officiel

### 2. ⏳ TripsPage.tsx
**Modifications Requises**:
- Remplacer ResponsivePageTemplate par GovPageHeader + GovPageWrapper
- Ajouter govStyles pour les boutons
- Tableau: fond bleu header, hover effects
- Boutons: style gouvernemental primaire
- Chip statuts: couleurs officielles

### 3. ⏳ TicketsPage.tsx
**Modifications Requises**:
- En-tête gouvernemental (🎫 GESTION DES BILLETS)
- Table avec header bleu (#003D66)
- Boutons primaires gouvernementaux
- Status chips avec couleurs TKF

### 4. ⏳ ParcelsPage.tsx
**Modifications Requises**:
- En-tête gouvernemental (📦 COLIS ET SUIVI)
- Tracking cards avec style gouvernemental
- Boutons actions en bleu officiel
- Map intégrée si disponible

### 5. ⏳ PaymentsPage.tsx
**Modifications Requises**:
- En-tête gouvernemental (💳 GESTION DES PAIEMENTS)
- Table paiements avec header bleu
- Status payments: completed=vert, pending=or, failed=rouge
- Boutons transactions en couleur officielle

### 6. ⏳ EmployeesPage.tsx
**Modifications Requises**:
- En-tête gouvernemental (👥 GESTION RESSOURCES HUMAINES)
- Cartes employés avec border #FFD700 (Or)
- Table avec header bleu
- Badges rôles/statuts

### 7. ⏳ CitiesPage.tsx
**Modifications Requises**:
- En-tête gouvernemental (🌍 VILLES ET COUVERTURE)
- Cartes villes avec border #007A5E (Vert)
- Grid responsive cities
- Statistiques par ville

## Composants et Styles à Réutiliser

### Imports Standards
```typescript
import { GovPageHeader, GovPageWrapper, GovPageFooter } from '../components'
import { govStyles } from '../styles/govStyles'
```

### Exemple de Wrappe
```tsx
<MainLayout>
  <GovPageWrapper maxWidth="lg">
    <GovPageHeader 
      title="Gestion des Trajets"
      icon="🚌"
      subtitle="Consultez et gérez l'ensemble de vos trajets"
      actions={[
        {
          label: 'Nouveau',
          icon: <AddIcon />,
          onClick: handleNew,
          variant: 'primary'
        }
      ]}
    />
    
    {/* Contenu */}
    
    <GovPageFooter text="Système de Gestion du Transport" />
  </GovPageWrapper>
</MainLayout>
```

## Couleurs à Appliquer

| Élément | Couleur | Code |
|---------|---------|------|
| Headers/Primaire | Bleu Gouvernemental | #003D66 |
| Danger/Alerte | Rouge Burkina | #CE1126 |
| Success/Vert | Vert Responsabilité | #007A5E |
| Warning/Or | Or Prestige | #FFD700 |
| Neutres | Gris | #666666 |
| Fond Clair | Blanc/Gris | #f5f5f5 |

## Boutons Standards

### Primary (Bleu)
- Actions principales
- Création/Sauvegarde
- Navigation importante

### Secondary (Gris)
- Actions secondaires
- Export/Téléchargement

### Danger (Rouge)
- Suppression
- Actions destructrices
- Alertes

## Mise en Œuvre

1. ✅ Styles créés: `govStyles.ts`
2. ✅ Composants créés: `GovPageComponents.tsx`
3. ⏳ À faire: Appliquer à chaque page

## Timeline

Phase 1 (Rapide):
- TripsPage: 15 min
- TicketsPage: 15 min
- PaymentsPage: 15 min

Phase 2 (Détails):
- ParcelsPage: 20 min (tracking)
- EmployeesPage: 20 min (cartes)
- CitiesPage: 20 min (maps)

**Total estimé**: ~2 heures pour 6 pages

EOF

cat PAGES_UPGRADE_PLAN.md

echo ""
echo "📊 Plan créé: PAGES_UPGRADE_PLAN.md"
echo ""
echo "Prochaines étapes:"
echo "1. Modifier TripsPage.tsx"
echo "2. Modifier TicketsPage.tsx"
echo "3. Modifier ParcelsPage.tsx"
echo "4. Modifier PaymentsPage.tsx"
echo "5. Modifier EmployeesPage.tsx"
echo "6. Modifier CitiesPage.tsx"
echo ""
echo "Chaque page utilisera:"
echo "  - GovPageHeader avec titre et icône"
echo "  - GovPageWrapper pour le contenu"
echo "  - GovPageFooter en bas"
echo "  - govStyles pour tous les composants"
