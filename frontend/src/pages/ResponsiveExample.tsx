// src/pages/ResponsiveExample.tsx
/**
 * Page exemple montrant comment utiliser tous les composants responsive
 * À adapter pour vos pages réelles
 */

import React, { useState } from 'react'
import { Box, Button, Card, CardContent, Chip, Stack, Typography, useTheme, useMediaQuery } from '@mui/material'
import { Add as AddIcon, Edit as EditIcon, Delete as DeleteIcon } from '@mui/icons-material'
import { MainLayout } from '../components/MainLayout'
import {
  ResponsivePageTemplate,
  ResponsiveTable,
  StatsGrid,
  ResponsiveFilters,
} from '../components'
import { responsiveStyles } from '../styles/responsiveStyles'

export const ResponsiveExample: React.FC = () => {
  const [search, setSearch] = useState('')
  const [filter, setFilter] = useState('all')
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'))

  // Données exemple
  const stats = [
    { label: 'Total', value: 1250, icon: '📊' },
    { label: 'Actif', value: 890, icon: '✅' },
    { label: 'Inactif', value: 360, icon: '⏸️' },
  ]

  const tableData = [
    {
      id: 1,
      name: 'Item 1',
      status: 'Actif',
      date: '2025-12-26',
      amount: '5000',
    },
    {
      id: 2,
      name: 'Item 2',
      status: 'Inactif',
      date: '2025-12-25',
      amount: '3000',
    },
    {
      id: 3,
      name: 'Item 3',
      status: 'Actif',
      date: '2025-12-24',
      amount: '7500',
    },
  ]

  return (
    <MainLayout>
      <ResponsivePageTemplate
        title="Exemple Page Responsive"
        subtitle="Découvrez comment utiliser les composants responsive"
        actions={[<Button startIcon={<AddIcon />}>Ajouter</Button>]}
      >
        {/* Section Statistiques */}
        <StatsGrid>
          {stats.map((stat) => (
            <Card key={stat.label} sx={responsiveStyles.statsCard}>
              <CardContent>
                <Typography variant="h3" sx={{ fontSize: { xs: '24px', md: '32px' } }}>
                  {stat.icon}
                </Typography>
                <Typography variant="h6" sx={{ mt: 2, fontWeight: 600 }}>
                  {stat.value}
                </Typography>
                <Typography variant="caption" color="textSecondary">
                  {stat.label}
                </Typography>
              </CardContent>
            </Card>
          ))}
        </StatsGrid>

        {/* Section Filtres */}
        <ResponsiveFilters
          fields={[
            {
              name: 'search',
              label: 'Recherche',
              value: search,
              onChange: setSearch,
            },
            {
              name: 'filter',
              label: 'Filtre',
              value: filter,
              onChange: setFilter,
              options: [
                { label: 'Tous', value: 'all' },
                { label: 'Actifs', value: 'active' },
                { label: 'Inactifs', value: 'inactive' },
              ],
            },
          ]}
          onApply={() => console.log('Appliquer filtres')}
          onReset={() => {
            setSearch('')
            setFilter('all')
          }}
        />

        {/* Section Tableau */}
        <Box sx={{ mt: 4 }}>
          <Typography variant="h6" sx={{ mb: 2, fontWeight: 600 }}>
            Liste des éléments
          </Typography>
          <ResponsiveTable
            columns={[
              { key: 'id', label: 'ID' },
              { key: 'name', label: 'Nom' },
              {
                key: 'status',
                label: 'Statut',
                render: (value) => (
                  <Chip
                    label={value}
                    color={value === 'Actif' ? 'success' : 'warning'}
                    size="small"
                    variant="outlined"
                  />
                ),
              },
              { key: 'date', label: 'Date' },
              { key: 'amount', label: 'Montant' },
              {
                key: 'actions',
                label: 'Actions',
                render: () => (
                  <Stack direction="row" spacing={1}>
                    <Button size="small" variant="text" startIcon={<EditIcon />}>
                      {!isMobile && 'Éditer'}
                    </Button>
                    <Button size="small" variant="text" color="error" startIcon={<DeleteIcon />}>
                      {!isMobile && 'Supprimer'}
                    </Button>
                  </Stack>
                ),
              },
            ]}
            data={tableData}
            emptyMessage="Aucune donnée"
          />
        </Box>
      </ResponsivePageTemplate>
    </MainLayout>
  )
}
