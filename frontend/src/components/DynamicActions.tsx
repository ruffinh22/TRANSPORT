import React from 'react'
import { Box, Typography, useTheme, useMediaQuery } from '@mui/material'
import {
  DirectionsRun as TripsIcon,
  ConfirmationNumber as TicketsIcon,
  LocalShipping as ParcelsIcon,
  Payment as PaymentsIcon,
  People as EmployeesIcon,
  LocationCity as CitiesIcon,
  BarChart as ReportsIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material'

interface ActionConfig {
  resource: string
  label: string
  icon: any
  path: string
  createPath?: string
  color?: string
  showLabel?: boolean
}

interface DynamicActionsProps {
  hasPermission: (action: 'view' | 'create' | 'edit' | 'delete', resource: string) => boolean
  navigate: (path: string) => void
  GovActionButton: React.FC<any>
  variant?: 'full' | 'compact'
  excludeResources?: string[]
}

const AVAILABLE_ACTIONS: ActionConfig[] = [
  {
    resource: 'trips',
    label: 'Trajet',
    icon: TripsIcon,
    path: '/trips',
    createPath: '/trips?action=create',
    color: '#003D66',
  },
  {
    resource: 'tickets',
    label: 'Billet',
    icon: TicketsIcon,
    path: '/tickets',
    createPath: '/tickets?action=create',
    color: '#CE1126',
  },
  {
    resource: 'parcels',
    label: 'Colis',
    icon: ParcelsIcon,
    path: '/parcels',
    createPath: '/parcels?action=create',
    color: '#007A5E',
  },
  {
    resource: 'payments',
    label: 'Paiem.',
    icon: PaymentsIcon,
    path: '/payments',
    createPath: '/payments?action=create',
    color: '#FF9800',
  },
  {
    resource: 'employees',
    label: 'Emp.',
    icon: EmployeesIcon,
    path: '/employees',
    createPath: '/employees?action=create',
    color: '#9C27B0',
  },
  {
    resource: 'cities',
    label: 'Villes',
    icon: CitiesIcon,
    path: '/cities',
    createPath: '/cities?action=create',
    color: '#00BCD4',
  },
  {
    resource: 'reports',
    label: 'Rapport',
    icon: ReportsIcon,
    path: '/reports',
    createPath: '/reports?action=create',
    color: '#4CAF50',
  },
  {
    resource: 'users',
    label: 'User',
    icon: EmployeesIcon,
    path: '/users',
    createPath: '/users?action=create',
    color: '#673AB7',
  },
]

/**
 * Composant qui génère dynamiquement les actions basées sur les permissions de l'utilisateur
 */
export const DynamicActions: React.FC<DynamicActionsProps> = ({
  hasPermission,
  navigate,
  GovActionButton,
  variant = 'full',
  excludeResources = [],
}) => {
  const theme = useTheme()
  const isMobile = useMediaQuery(theme.breakpoints.down('sm'))

  // Filtrer les actions disponibles basées sur les permissions
  const availableActions = AVAILABLE_ACTIONS.filter(action => {
    // Exclure les ressources spécifiées
    if (excludeResources.includes(action.resource)) {
      return false
    }

    // Vérifier si l'utilisateur a au moins create ou edit pour cette ressource
    return hasPermission('create', action.resource) || hasPermission('edit', action.resource)
  })

  // Si pas d'actions disponibles
  if (availableActions.length === 0) {
    return (
      <Box
        sx={{
          p: { xs: 1.5, sm: 2, md: 3 },
          backgroundColor: '#f0f0f0',
          borderRadius: '8px',
          textAlign: 'center',
        }}
      >
        <Typography
          variant="body2"
          sx={{
            color: '#666',
            fontSize: { xs: '0.75rem', sm: '0.85rem', md: '0.95rem' },
            lineHeight: 1.4,
          }}
        >
          👁️ Lecture seule
        </Typography>
      </Box>
    )
  }

  return (
    <Box
      sx={{
        display: 'grid',
        gridTemplateColumns:
          variant === 'compact'
            ? { xs: 'repeat(2, 1fr)', sm: 'repeat(3, 1fr)', md: 'repeat(4, 1fr)' }
            : { xs: '1fr', sm: 'repeat(2, 1fr)', md: 'repeat(4, 1fr)' },
        gap: { xs: 1, sm: 1.5, md: 2 },
      }}
    >
      {availableActions.map((action) => {
        const canCreate = hasPermission('create', action.resource)
        const canEdit = hasPermission('edit', action.resource)
        const label = canCreate ? `➕ ${action.label}` : `✏️ ${action.label}`
        const path = canCreate && action.createPath ? action.createPath : action.path

        return (
          <GovActionButton
            key={action.resource}
            label={label}
            icon={action.icon}
            onClick={() => navigate(path)}
          />
        )
      })}
    </Box>
  )
}

export default DynamicActions
