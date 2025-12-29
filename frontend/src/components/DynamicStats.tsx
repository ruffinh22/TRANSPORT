import React from 'react'
import { Box, Typography } from '@mui/material'
import {
  DirectionsRun as TripsIcon,
  ConfirmationNumber as TicketsIcon,
  LocalShipping as ParcelsIcon,
  People as EmployeesIcon,
  LocationCity as CitiesIcon,
  TrendingUp as RevenueIcon,
} from '@mui/icons-material'

interface StatItem {
  resource: string
  title: string
  value: number
  icon: any
  color: string
  path?: string
}

interface DynamicStatsProps {
  hasPermission: (action: 'view' | 'create' | 'edit' | 'delete', resource: string) => boolean
  stats: Record<string, number>
  navigate: (path: string) => void
  GovStatCard: React.FC<any>
  layout?: 'full' | 'compact'
}

/**
 * Composant qui affiche dynamiquement les statistiques selon les permissions
 */
export const DynamicStats: React.FC<DynamicStatsProps> = ({
  hasPermission,
  stats,
  navigate,
  GovStatCard,
  layout = 'full',
}) => {
  // Définir les statistiques disponibles
  const availableStats: StatItem[] = [
    {
      resource: 'trips',
      title: 'Trajets',
      value: stats.trips || 0,
      icon: TripsIcon,
      color: '#003D66',
      path: '/trips',
    },
    {
      resource: 'tickets',
      title: 'Billets',
      value: stats.tickets || 0,
      icon: TicketsIcon,
      color: '#CE1126',
      path: '/tickets',
    },
    {
      resource: 'parcels',
      title: 'Colis',
      value: stats.parcels || 0,
      icon: ParcelsIcon,
      color: '#007A5E',
      path: '/parcels',
    },
    {
      resource: 'payments',
      title: 'Paiements',
      value: stats.payments || 0,
      icon: TrendingIcon,
      color: '#003D66',
      path: '/payments',
    },
    {
      resource: 'employees',
      title: 'Employés',
      value: stats.employees || 0,
      icon: EmployeesIcon,
      color: '#FFD700',
      path: '/employees',
    },
    {
      resource: 'cities',
      title: 'Villes',
      value: stats.cities || 0,
      icon: CitiesIcon,
      color: '#CE1126',
      path: '/cities',
    },
    {
      resource: 'revenue',
      title: 'Chiffre d\'Affaires',
      value: stats.revenue || 0,
      icon: RevenueIcon,
      color: '#003D66',
      path: undefined,
    },
  ]

  // Filtrer les stats selon les permissions (view)
  const visibleStats = availableStats.filter(stat => hasPermission('view', stat.resource))

  if (visibleStats.length === 0) {
    return (
      <Box sx={{ textAlign: 'center', p: 3 }}>
        <Typography color="textSecondary">Aucune statistique disponible</Typography>
      </Box>
    )
  }

  // Déterminer la grille selon le layout
  const gridProps = {
    display: 'grid',
    gap: { xs: 1, sm: 1.5, md: 2.5 },
    mb: { xs: 2, sm: 2.5, md: 4 },
    ...(layout === 'compact'
      ? {
          gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(3, 1fr)' },
        }
      : {
          gridTemplateColumns: { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' },
        }),
  }

  return (
    <Box sx={gridProps}>
      {visibleStats.map((stat) => (
        <GovStatCard
          key={stat.resource}
          title={stat.title}
          value={
            stat.resource === 'revenue'
              ? stat.value.toLocaleString('fr-FR')
              : stat.value
          }
          icon={stat.icon}
          onClick={stat.path ? () => navigate(stat.path) : undefined}
          color={stat.color}
        />
      ))}
    </Box>
  )
}

export default DynamicStats
