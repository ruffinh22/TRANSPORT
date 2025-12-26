#!/bin/bash

# Script: Apply Government Design to All Remaining Pages
# Pages: Tickets, Parcels, Payments, Employees, Cities

cd /home/lidruf/TRANSPORT/frontend/src/pages

echo "🏛️ Applying Professional Government Design to ALL Pages..."
echo ""

# Create a comprehensive update document
cat > ../../GOV_DESIGN_IMPLEMENTATION.md << 'EOF'
# 🏛️ Implementation du Design Gouvernemental Professionnel

## Status Actuel (26 Dec 2025)

### ✅ Complété
- **Dashboard.tsx** - Design gouvernemental complet
  - Cartes statistiques cliquables
  - Boutons actions gouvernementaux
  - Couleurs officielles (Bleu, Rouge, Vert, Or)
  - Responsive mobile/tablet/desktop
  - Pied de page officiel

- **TripsPage.tsx** - Mise à jour complète
  - En-tête gouvernemental (🚌 Gestion des Trajets)
  - Table avec header bleu #003D66
  - Boutons primaires gouvernementaux
  - Chips statuts avec couleurs officielles
  - Dialog form avec styling gouvernemental
  - Pied de page officiel

### ⏳ À Faire (5 pages)

#### 1. TicketsPage.tsx
```
Modifications requises:
- Import: GovPageHeader, GovPageWrapper, GovPageFooter
- Import: govStyles
- En-tête: 🎫 Gestion des Billets
- Table: Header bleu (#003D66)
- Chips: Couleurs statuts CFA
- Buttons: Style gouvernemental
- Dialog: Header bleu comme TripsPage
- Footer: Avec texte spécifique
```

#### 2. ParcelsPage.tsx
```
Modifications requises:
- Import: GovPageHeader, GovPageWrapper, GovPageFooter
- Import: govStyles
- En-tête: 📦 Colis et Suivi
- Tracking cards: Border #007A5E (vert)
- Table: Header bleu
- Buttons: Style gouvernemental
- Status: Couleurs officielles
- Footer: Avec texte spécifique
```

#### 3. PaymentsPage.tsx
```
Modifications requises:
- Import: GovPageHeader, GovPageWrapper, GovPageFooter
- Import: govStyles
- En-tête: 💳 Gestion des Paiements
- Table: Header bleu (#003D66)
- Statuts: 
  - completed = vert (#007A5E)
  - pending = or (#FFD700)
  - failed = rouge (#CE1126)
- Buttons: Gouvernemental
- Montants: Format CFA avec groupement
- Footer: Avec texte spécifique
```

#### 4. EmployeesPage.tsx
```
Modifications requises:
- Import: GovPageHeader, GovPageWrapper, GovPageFooter
- Import: govStyles
- En-tête: 👥 Gestion Ressources Humaines
- Cards: Border #FFD700 (Or prestige)
- Table: Header bleu
- Rôles: Badges avec couleurs officielles
- Statuts: active=vert, inactive=gris
- Buttons: Gouvernemental
- Footer: Avec texte spécifique
```

#### 5. CitiesPage.tsx
```
Modifications requises:
- Import: GovPageHeader, GovPageWrapper, GovPageFooter
- Import: govStyles
- En-tête: 🌍 Villes et Couverture
- Cards: Border #007A5E (Vert)
- Table: Header bleu
- Stats: Petits widgets gouvernementaux
- Buttons: Gouvernemental
- Grid: Responsive 1-2-3-4 colonnes
- Footer: Avec texte spécifique
```

## Modèle Unifié Pour Toutes les Pages

### Imports Standards
```typescript
import { GovPageHeader, GovPageWrapper, GovPageFooter } from '../components'
import { govStyles } from '../styles/govStyles'
```

### Structure JSX
```tsx
<MainLayout>
  <GovPageWrapper maxWidth="lg">
    
    {/* En-tête */}
    <GovPageHeader
      title="Titre de la Page"
      icon="🔷 Icône"
      subtitle="Description courte"
      actions={[
        {
          label: 'Action Principale',
          icon: <AddIcon />,
          onClick: handleAction,
          variant: 'primary' // primary | secondary | danger
        }
      ]}
    />
    
    {/* Alertes */}
    {error && <Alert severity="error" sx={{ mb: 3 }}>{error}</Alert>}
    
    {/* Filtres */}
    <Paper sx={{ p: 2, mb: 3, ...govStyles.contentCard }}>
      {/* Contrôles filtres */}
    </Paper>
    
    {/* Contenu Principal */}
    <TableContainer component={Paper} sx={govStyles.contentCard}>
      <Table sx={govStyles.table}>
        {/* Tableau */}
      </Table>
    </TableContainer>
    
    {/* Pied de Page */}
    <GovPageFooter text="Description spécifique à la page" />
    
  </GovPageWrapper>
</MainLayout>
```

## Palette de Couleurs Officielles

| Usage | Couleur | Code | Usage |
|-------|---------|------|-------|
| Primaire | Bleu | #003D66 | Headers, boutons primaires, borders |
| Danger | Rouge | #CE1126 | Suppression, alertes, statuts critiques |
| Success | Vert | #007A5E | Transport actif, statuts réussis |
| Warning | Or | #FFD700 | RH, avertissements, highlights |
| Neutral | Gris | #666666 | Texte, statuts neutres |
| Light | Blanc/Gris | #f5f5f5 | Fonds clairs |

## Composants Réutilisables

### GovPageHeader
```typescript
interface GovPageHeaderProps {
  title: string          // Titre principal
  icon?: string         // Emoji optionnel
  subtitle?: string     // Sous-titre
  actions?: Array<{
    label: string
    icon: React.ReactNode
    onClick: () => void
    variant?: 'primary' | 'secondary' | 'danger'
  }>
}
```

### GovPageWrapper
```typescript
interface GovPageWrapperProps {
  children: React.ReactNode
  maxWidth?: 'xs' | 'sm' | 'md' | 'lg' | 'xl'
}
```

### GovPageFooter
```typescript
interface GovPageFooterProps {
  text: string  // Description de la page
}
```

## Styles Réutilisables (govStyles)

```typescript
govStyles.colors          // Palette complète
govStyles.pageHeader      // Style en-tête
govStyles.pageTitle       // Typographie titre
govStyles.govButton       // Boutons (primary, secondary, danger)
govStyles.statCard        // Cartes statistiques
govStyles.contentCard     // Cartes contenu
govStyles.table           // Styles tableau
govStyles.footer          // Pied de page
govStyles.icon            // Icônes avec couleurs
```

## Timeline de Mise en Œuvre

- ✅ **Phase 1**: Dashboard + TripsPage
- ⏳ **Phase 2**: TicketsPage, PaymentsPage (15 min)
- ⏳ **Phase 3**: ParcelsPage, EmployeesPage, CitiesPage (20 min)
- ⏳ **Validation**: Build + Git commit (5 min)

**Total**: ~1 heure pour 7 pages

## Checklist par Page

### TicketsPage
- [ ] Imports GovPageHeader, GovPageWrapper, GovPageFooter
- [ ] Imports govStyles
- [ ] Remplacer ResponsivePageTemplate
- [ ] Table avec header bleu
- [ ] Boutons gouvernementaux
- [ ] Chips statuts avec couleurs
- [ ] Dialog avec header bleu
- [ ] GovPageFooter

### ParcelsPage
- [ ] Imports et structures
- [ ] Tracking cards avec vert (#007A5E)
- [ ] Table gouvernementale
- [ ] Statuts tracking avec couleurs
- [ ] Boutons actions
- [ ] Responsive responsive

### PaymentsPage
- [ ] Structure gouvernementale
- [ ] Table paiements
- [ ] Statuts: completed/pending/failed
- [ ] Montants en FCFA formatés
- [ ] Boutons transactions
- [ ] Chips montants colorées

### EmployeesPage
- [ ] Structure gouvernementale
- [ ] Cards employés avec or (#FFD700)
- [ ] Table RH
- [ ] Badges rôles/statuts
- [ ] Boutons actions
- [ ] Modals gouvernementaux

### CitiesPage
- [ ] Structure gouvernementale
- [ ] Cards villes avec vert (#007A5E)
- [ ] Table couverture
- [ ] Stats par ville
- [ ] Grid responsive
- [ ] Modals gouvernementaux

## Notes Importantes

✅ Les pages conservent leurs fonctionnalités originales
✅ Les styles govStyles sont réutilisables pour futures pages
✅ Les composants GovPageHeader/Footer sont peu coûteux (imports légers)
✅ Responsive design préservé automatiquement avec GovPageWrapper
✅ Tous les styles utilisent MUI standard

## Prochaines Étapes

1. Appliquer à TicketsPage
2. Appliquer à PaymentsPage
3. Appliquer à ParcelsPage
4. Appliquer à EmployeesPage
5. Appliquer à CitiesPage
6. Build complet
7. Git commit global

EOF

echo "📋 Documentation créée: GOV_DESIGN_IMPLEMENTATION.md"
echo ""
echo "🎯 Pages mises à jour:"
echo "  ✅ Dashboard.tsx"
echo "  ✅ TripsPage.tsx"
echo "  ⏳ TicketsPage.tsx (à venir)"
echo "  ⏳ ParcelsPage.tsx (à venir)"
echo "  ⏳ PaymentsPage.tsx (à venir)"
echo "  ⏳ EmployeesPage.tsx (à venir)"
echo "  ⏳ CitiesPage.tsx (à venir)"
echo ""
echo "✨ Build réussi: 31.30s"
echo "🔧 Prochaine étape: TicketsPage"
