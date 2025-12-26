# 📱 Guide Responsive Design Pro - TKF

## 🎯 Vue d'ensemble

Un système cohérent et professionnel pour rendre toutes les pages **responsive** sur mobile, tablette et desktop.

---

## 📦 Composants Disponibles

### 1. **ResponsivePageTemplate** - Structure de base
Enveloppe chaque page avec header, titre et actions responsive.

```tsx
import { ResponsivePageTemplate } from '../components'

export const MyPage = () => (
  <ResponsivePageTemplate
    title="Mon Titre"
    subtitle="Sous-titre optionnel"
    actions={[
      <Button startIcon={<AddIcon />}>Ajouter</Button>
    ]}
  >
    {/* Contenu de la page */}
  </ResponsivePageTemplate>
)
```

### 2. **ResponsiveTable** - Tableau qui devient cartes sur mobile
Affiche automatiquement un tableau sur desktop et des cartes sur mobile.

```tsx
import { ResponsiveTable } from '../components'

<ResponsiveTable
  columns={[
    { key: 'name', label: 'Nom' },
    { key: 'email', label: 'Email' },
    { key: 'status', label: 'Statut', render: (val) => <Chip label={val} /> },
  ]}
  data={myData}
  emptyMessage="Aucune donnée"
/>
```

### 3. **Grilles Responsive** - Layouts responsives prédéfinis
Différents types de grilles pour différents besoins.

```tsx
import { StatsGrid, CardGrid, DetailGrid } from '../components'

// 3 colonnes (stats)
<StatsGrid>
  {stats.map((stat) => <StatCard key={stat.id} {...stat} />)}
</StatsGrid>

// 2 colonnes (cartes)
<CardGrid>
  {cards.map((card) => <Card key={card.id}>{card.content}</Card>)}
</CardGrid>

// 4 colonnes (détails)
<DetailGrid>
  {details.map((detail) => <DetailCard key={detail.id} {...detail} />)}
</DetailGrid>
```

### 4. **ResponsiveFilters** - Filtres qui se cachent sur mobile
Affiche les filtres dans un drawer/collapse sur mobile.

```tsx
import { ResponsiveFilters } from '../components'

<ResponsiveFilters
  fields={[
    { name: 'search', label: 'Recherche', value: search, onChange: setSearch },
    { name: 'status', label: 'Statut', value: status, onChange: setStatus },
  ]}
  onApply={() => applyFilters()}
  onReset={() => resetFilters()}
/>
```

---

## 🎨 Styles Réutilisables

Importez `responsiveStyles` pour des styles cohérents.

```tsx
import { responsiveStyles } from '../styles/responsiveStyles'

<Box sx={responsiveStyles.card}>Contenu</Box>
<Box sx={responsiveStyles.pageTitle}>Titre</Box>
<Box sx={responsiveStyles.flexBetween}>Flex avec gap responsive</Box>
<Box sx={responsiveStyles.actionButtons}>Boutons empilés sur mobile</Box>
```

---

## 📏 Breakpoints MUI Standard

| Device | Taille | Breakpoint |
|--------|--------|-----------|
| Mobile | < 600px | `xs` |
| Tablet | 600px - 960px | `sm` |
| Desktop | 960px - 1280px | `md` |
| Large | 1280px - 1920px | `lg` |
| XL | > 1920px | `xl` |

---

## 🔧 Adapter une page existante

### Avant (non-responsive)
```tsx
export const TripsPage = () => (
  <Box sx={{ p: 2 }}>
    <Typography variant="h4">Trajets</Typography>
    <Table>
      {/* ... */}
    </Table>
  </Box>
)
```

### Après (responsive)
```tsx
import { ResponsivePageTemplate, ResponsiveTable, ResponsiveFilters } from '../components'
import { responsiveStyles } from '../styles/responsiveStyles'

export const TripsPage = () => {
  const [search, setSearch] = useState('')

  return (
    <MainLayout>
      <ResponsivePageTemplate
        title="Gestion des Trajets"
        subtitle="Consultez et gérez vos trajets"
        actions={[<Button startIcon={<AddIcon />}>Nouveau trajet</Button>]}
      >
        <ResponsiveFilters
          fields={[
            { name: 'search', label: 'Recherche', value: search, onChange: setSearch }
          ]}
        />

        <ResponsiveTable
          columns={[
            { key: 'departure_city', label: 'Départ' },
            { key: 'arrival_city', label: 'Arrivée' },
            { key: 'departure_date', label: 'Date' },
            { key: 'status', label: 'Statut', render: (val) => <Chip label={val} /> },
            { key: 'actions', label: 'Actions', render: () => <ActionButtons /> },
          ]}
          data={trips}
        />
      </ResponsivePageTemplate>
    </MainLayout>
  )
}
```

---

## ✅ Checklist Responsive

- [ ] Utiliser `ResponsivePageTemplate` pour la structure
- [ ] Utiliser `ResponsiveTable` pour les tableaux
- [ ] Utiliser `StatsGrid/CardGrid/DetailGrid` pour les grilles
- [ ] Utiliser `ResponsiveFilters` pour les filtres
- [ ] Tester sur mobile (< 600px)
- [ ] Tester sur tablette (600px - 960px)
- [ ] Tester sur desktop (> 960px)

---

## 🚀 Exemple Complet

Voir `/frontend/src/pages/ResponsiveExample.tsx` pour un exemple complet avec tous les composants.

```bash
# Tester l'exemple
cd frontend
yarn dev
# Ouvrir http://localhost:3000/example
```

---

## 📱 Comportements Responsive

### Sur Mobile (xs)
- Navigation: Sidebar qui se ferme
- Grilles: 1 colonne pleine largeur
- Tableau: Cartes empilées
- Filtres: Drawer/Collapse masqué
- Boutons: Empilés verticalement
- Spacing: Réduit (1x, 2x)

### Sur Tablette (sm-md)
- Navigation: Sidebar visible
- Grilles: 2 colonnes
- Tableau: Tableau compact
- Filtres: Visibles mais compacts
- Boutons: Côte à côte
- Spacing: Normal

### Sur Desktop (lg+)
- Navigation: Sidebar normal
- Grilles: 3-4 colonnes
- Tableau: Tableau plein
- Filtres: Tous visibles
- Boutons: Alignés horizontal
- Spacing: Optimisé

---

## 🎯 Bonnes pratiques

1. **Toujours utiliser ResponsivePageTemplate** comme base
2. **Utiliser les grilles prédéfinies** (StatsGrid, CardGrid, DetailGrid)
3. **Éviter les marges fixes** - utiliser `sx={{ p: { xs: 1, md: 3 } }}`
4. **Tester sur tous les devices** - incluant landscape/portrait
5. **Utiliser les composants Responsive** plutôt que custom
6. **Respecter les breakpoints MUI** - ne pas créer de custom breakpoints

---

## 🐛 Troubleshooting

**Tableau ne se convertit pas en cartes?**
```tsx
// Vérifier que ResponsiveTable est importé correctement
import { ResponsiveTable } from '../components'
```

**Grille pas responsive?**
```tsx
// Utiliser les grilles prédéfinies
<StatsGrid>  {/* 3 colonnes */}
<CardGrid>   {/* 2 colonnes */}
<DetailGrid> {/* 4 colonnes */}
```

**Filtres toujours visibles sur mobile?**
```tsx
// ResponsiveFilters gère ça automatiquement
// Vérifier useMediaQuery si custom:
const isMobile = useMediaQuery(theme.breakpoints.down('sm'))
```
