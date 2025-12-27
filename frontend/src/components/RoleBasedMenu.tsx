import React from 'react'
import { List, ListItem, ListItemButton, ListItemIcon, ListItemText, Collapse } from '@mui/material'
import { useRoleBasedAccess } from '../hooks'
import DashboardIcon from '@mui/icons-material/Dashboard'
import DirectionsBusIcon from '@mui/icons-material/DirectionsBus'
import ConfirmationNumberIcon from '@mui/icons-material/ConfirmationNumber'
import LocalShippingIcon from '@mui/icons-material/LocalShipping'
import PaymentIcon from '@mui/icons-material/Payment'
import PeopleIcon from '@mui/icons-material/People'
import LocationCityIcon from '@mui/icons-material/LocationCity'
import AssessmentIcon from '@mui/icons-material/Assessment'
import SettingsIcon from '@mui/icons-material/Settings'
import ExpandLess from '@mui/icons-material/ExpandLess'
import ExpandMore from '@mui/icons-material/ExpandMore'
import { govStyles } from '../styles/govStyles'

interface MenuItem {
  label: string
  icon: React.ReactNode
  path: string
  roles: string[] // Rôles requis pour voir ce menu
  subItems?: MenuItem[]
}

interface RoleBasedMenuProps {
  onNavigate?: (path: string) => void
  collapsed?: boolean
}

/**
 * Composant de menu dynamique basé sur les rôles
 */
export const RoleBasedMenu: React.FC<RoleBasedMenuProps> = ({ onNavigate, collapsed = false }) => {
  const { hasRole, hasAnyRole } = useRoleBasedAccess()
  const [expandedSections, setExpandedSections] = React.useState<string[]>(['general'])

  // Définir tous les menuItems disponibles
  const allMenuItems: MenuItem[] = [
    {
      label: 'Tableau de Bord',
      icon: <DashboardIcon />,
      path: '/dashboard',
      roles: ['SUPER_ADMIN', 'ADMIN', 'MANAGER', 'COMPTABLE', 'GUICHETIER', 'CHAUFFEUR', 'CONTROLEUR', 'GESTIONNAIRE_COURRIER'],
    },
    {
      label: 'Gestion Trajets',
      icon: <DirectionsBusIcon />,
      path: '/trips',
      roles: ['SUPER_ADMIN', 'ADMIN', 'MANAGER', 'CHAUFFEUR'],
    },
    {
      label: 'Billetterie',
      icon: <ConfirmationNumberIcon />,
      path: '/tickets',
      roles: ['SUPER_ADMIN', 'ADMIN', 'MANAGER', 'GUICHETIER', 'CONTROLEUR'],
    },
    {
      label: 'Colis & Courrier',
      icon: <LocalShippingIcon />,
      path: '/parcels',
      roles: ['SUPER_ADMIN', 'ADMIN', 'MANAGER', 'GESTIONNAIRE_COURRIER'],
    },
    {
      label: 'Paiements',
      icon: <PaymentIcon />,
      path: '/payments',
      roles: ['SUPER_ADMIN', 'ADMIN', 'COMPTABLE', 'GUICHETIER'],
    },
    {
      label: 'Personnel',
      icon: <PeopleIcon />,
      path: '/employees',
      roles: ['SUPER_ADMIN', 'ADMIN', 'MANAGER'],
    },
    {
      label: 'Villes & Routes',
      icon: <LocationCityIcon />,
      path: '/cities',
      roles: ['SUPER_ADMIN', 'ADMIN', 'MANAGER'],
    },
    {
      label: 'Rapports',
      icon: <AssessmentIcon />,
      path: '/reports',
      roles: ['SUPER_ADMIN', 'ADMIN', 'MANAGER', 'COMPTABLE'],
    },
    {
      label: 'Paramètres',
      icon: <SettingsIcon />,
      path: '/settings',
      roles: ['SUPER_ADMIN', 'ADMIN'],
    },
  ]

  // Filtrer les items du menu selon les rôles de l'utilisateur
  const visibleMenuItems = allMenuItems.filter((item) => hasAnyRole(item.roles))

  const toggleSection = (sectionLabel: string) => {
    setExpandedSections((prev) =>
      prev.includes(sectionLabel) ? prev.filter((s) => s !== sectionLabel) : [...prev, sectionLabel]
    )
  }

  const handleItemClick = (path: string) => {
    if (onNavigate) {
      onNavigate(path)
    } else {
      // Naviguer avec React Router
      window.location.href = path
    }
  }

  return (
    <List>
      {visibleMenuItems.map((item) => (
        <React.Fragment key={item.path}>
          <ListItem disablePadding>
            <ListItemButton
              onClick={() => handleItemClick(item.path)}
              sx={{
                color: govStyles.colors.text,
                '&:hover': {
                  backgroundColor: `${govStyles.colors.primary}15`,
                  color: govStyles.colors.primary,
                },
                py: collapsed ? 1 : 1.5,
              }}
            >
              <ListItemIcon
                sx={{
                  color: govStyles.colors.primary,
                  minWidth: collapsed ? 40 : 56,
                }}
              >
                {item.icon}
              </ListItemIcon>
              {!collapsed && <ListItemText primary={item.label} />}
            </ListItemButton>
          </ListItem>
        </React.Fragment>
      ))}
    </List>
  )
}

export default RoleBasedMenu
