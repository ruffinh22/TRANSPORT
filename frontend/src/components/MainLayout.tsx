import React, { useState } from 'react'
import {
  AppBar,
  Toolbar,
  Drawer,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  Box,
  CssBaseline,
  Typography,
  IconButton,
  Menu,
  MenuItem,
  Avatar,
  Divider,
  Container,
} from '@mui/material'
import {
  Menu as MenuIcon,
  Close as CloseIcon,
  Dashboard as DashboardIcon,
  DirectionsRun as TripsIcon,
  ConfirmationNumber as TicketsIcon,
  LocalShipping as ParcelsIcon,
  Payment as PaymentsIcon,
  People as EmployeesIcon,
  LocationCity as CitiesIcon,
  Assessment as ReportsIcon,
  Settings as SettingsIcon,
  Logout as LogoutIcon,
  Home as HomeIcon,
  Notifications as NotificationsIcon,
  KeyboardArrowDown as KeyboardArrowDownIcon,
} from '@mui/icons-material'
import { useNavigate } from 'react-router-dom'
import { useAppDispatch, useAppSelector } from '../hooks'
import { logout } from '../store/authSlice'
import { GovernmentHeader } from './GovernmentHeader'
import { GovernmentFooter } from './GovernmentFooter'

const DRAWER_WIDTH = 280

interface MainLayoutProps {
  children: React.ReactNode
  hideGovernmentHeader?: boolean
}

// Permissions par rôle avec actions CRUD
interface RolePermissions {
  view: string[]
  create: string[]
  edit: string[]
  delete: string[]
}

const ROLE_PERMISSIONS: Record<string, RolePermissions> = {
  ADMIN: {
    view: ['dashboard', 'trips', 'tickets', 'parcels', 'payments', 'revenue', 'employees', 'cities', 'reports', 'manage_users'],
    create: ['trips', 'tickets', 'parcels', 'payments', 'employees', 'cities', 'users'],
    edit: ['trips', 'tickets', 'parcels', 'payments', 'employees', 'cities', 'users'],
    delete: ['trips', 'tickets', 'parcels', 'payments', 'employees', 'cities', 'users'],
  },
  COMPTABLE: {
    view: ['dashboard', 'payments', 'revenue', 'reports', 'employees'],
    create: ['payments', 'reports'],
    edit: ['payments', 'reports'],
    delete: [],
  },
  GUICHETIER: {
    view: ['dashboard', 'tickets', 'parcels', 'trips'],
    create: ['tickets', 'parcels'],
    edit: ['tickets', 'parcels'],
    delete: [],
  },
  CHAUFFEUR: {
    view: ['dashboard', 'trips', 'tickets'],
    create: [],
    edit: ['trips'],
    delete: [],
  },
  CONTROLEUR: {
    view: ['dashboard', 'tickets', 'trips', 'employees'],
    create: [],
    edit: ['trips', 'tickets'],
    delete: [],
  },
  GESTIONNAIRE_COURRIER: {
    view: ['dashboard', 'parcels', 'cities'],
    create: ['parcels'],
    edit: ['parcels'],
    delete: [],
  },
  CLIENT: {
    view: ['dashboard', 'trips', 'tickets', 'parcels'],
    create: [],
    edit: [],
    delete: [],
  },
}

const menuItems = [
  { label: 'Tableau de bord', icon: <DashboardIcon />, path: '/dashboard', resource: 'dashboard' },
  { label: 'Trajets', icon: <TripsIcon />, path: '/trips', resource: 'trips' },
  { label: 'Billets', icon: <TicketsIcon />, path: '/tickets', resource: 'tickets' },
  { label: 'Colis', icon: <ParcelsIcon />, path: '/parcels', resource: 'parcels' },
  { label: 'Paiements', icon: <PaymentsIcon />, path: '/payments', resource: 'payments' },
  { label: 'Employés', icon: <EmployeesIcon />, path: '/employees', resource: 'employees' },
  { label: 'Villes', icon: <CitiesIcon />, path: '/cities', resource: 'cities' },
  { label: 'Rapports', icon: <ReportsIcon />, path: '/reports', resource: 'reports' },
]

const settingsItems = [
  { label: 'Paramètres', icon: <SettingsIcon />, path: '/settings' },
]

export const MainLayout: React.FC<MainLayoutProps> = ({ children, hideGovernmentHeader = false }) => {
  const navigate = useNavigate()
  const dispatch = useAppDispatch()
  const { user } = useAppSelector((state) => state.auth)
  const [openDrawer, setOpenDrawer] = useState(true)
  const [mobileOpen, setMobileOpen] = useState(false)
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)
  const [notificationAnchor, setNotificationAnchor] = useState<null | HTMLElement>(null)

  // Déterminer le rôle principal de l'utilisateur
  const userRole = user?.roles?.[0] || 'CLIENT'
  const userPermissions = ROLE_PERMISSIONS[userRole as keyof typeof ROLE_PERMISSIONS] || ROLE_PERMISSIONS.CLIENT

  // Fonction pour vérifier les permissions
  const hasPermission = (action: 'view' | 'create' | 'edit' | 'delete', resource: string): boolean => {
    return userPermissions[action].includes(resource)
  }

  // Filtrer les items du menu selon les permissions
  const visibleMenuItems = menuItems.filter((item) => hasPermission('view', item.resource))

  const handleDrawerToggle = () => {
    setOpenDrawer(!openDrawer)
  }

  const handleMobileDrawerToggle = () => {
    setMobileOpen(!mobileOpen)
  }

  const handleMenuOpen = (event: React.MouseEvent<HTMLElement>) => {
    setAnchorEl(event.currentTarget)
  }

  const handleMenuClose = () => {
    setAnchorEl(null)
  }

  const handleNotificationOpen = (event: React.MouseEvent<HTMLElement>) => {
    setNotificationAnchor(event.currentTarget)
  }

  const handleNotificationClose = () => {
    setNotificationAnchor(null)
  }

  const handleLogout = async () => {
    await dispatch(logout())
    navigate('/login')
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <CssBaseline />

      {/* Government Header - Desktop Only */}
      {!hideGovernmentHeader && (
        <Box sx={{ display: { xs: 'none', md: 'block' } }}>
          <GovernmentHeader language="fr" />
        </Box>
      )}

      {/* App Bar */}
      <AppBar
        position="static"
        sx={{
          background: 'linear-gradient(135deg, #003D66 0%, #001f3f 100%)',
          boxShadow: '0 4px 16px rgba(0, 0, 0, 0.15)',
          borderBottom: '3px solid #CE1126',
        }}
      >
        <Container maxWidth="lg">
          <Toolbar disableGutters sx={{ py: { xs: 0.75, md: 1.25 }, minHeight: { xs: '64px', md: '72px' }, display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            {/* Left Section - Logo & Menu Toggle */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: { xs: 1, md: 2 } }}>
              <IconButton
                color="inherit"
                aria-label="toggle drawer"
                onClick={handleMobileDrawerToggle}
                sx={{ 
                  mr: { xs: 0, md: 1 },
                  display: { xs: 'flex', md: 'none' },
                  backgroundColor: 'rgba(206, 17, 38, 0.3)',
                  '&:hover': {
                    backgroundColor: 'rgba(206, 17, 38, 0.5)',
                  }
                }}
              >
                {mobileOpen ? <CloseIcon /> : <MenuIcon />}
              </IconButton>

              {/* Bouton Accueil */}
              <IconButton
                color="inherit"
                onClick={() => navigate('/dashboard')}
                title="Aller à l'Accueil"
                sx={{
                  display: { xs: 'none', md: 'flex' },
                  backgroundColor: 'rgba(206, 17, 38, 0.2)',
                  '&:hover': {
                    backgroundColor: 'rgba(206, 17, 38, 0.4)',
                  },
                }}
              >
                <HomeIcon sx={{ fontSize: '1.5rem' }} />
              </IconButton>

              {/* Logo & Title */}
              <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
                <Typography 
                  variant="h6" 
                  component="div" 
                  sx={{ 
                    fontWeight: 800, 
                    fontSize: { xs: '1rem', md: '1.3rem' },
                    letterSpacing: '2px',
                    color: '#ffffff',
                    textTransform: 'uppercase',
                  }}
                >
                  🏛️ TKF
                </Typography>
                <Divider orientation="vertical" sx={{ height: 24, backgroundColor: 'rgba(206, 17, 38, 0.5)' }} />
                <Typography 
                  variant="body2" 
                  sx={{ 
                    fontWeight: 600,
                    fontSize: { xs: '0.7rem', md: '0.9rem' },
                    letterSpacing: '0.5px',
                    color: 'rgba(255, 255, 255, 0.85)',
                    display: { xs: 'none', sm: 'block' },
                  }}
                >
                  GESTION DU TRANSPORT
                </Typography>
              </Box>
            </Box>

            {/* Right Section - User Info, Notifications & Menu */}
            <Box sx={{ display: 'flex', alignItems: 'center', gap: { xs: 1, md: 2.5 }, ml: 'auto' }}>

              {/* Notifications Button */}
              <IconButton
                color="inherit"
                onClick={handleNotificationOpen}
                sx={{
                  position: 'relative',
                  backgroundColor: 'rgba(206, 17, 38, 0.2)',
                  '&:hover': {
                    backgroundColor: 'rgba(206, 17, 38, 0.4)',
                  },
                }}
                title="Notifications"
              >
                <NotificationsIcon sx={{ fontSize: '1.3rem' }} />
                <Box
                  sx={{
                    position: 'absolute',
                    top: 6,
                    right: 6,
                    width: 16,
                    height: 16,
                    backgroundColor: '#CE1126',
                    borderRadius: '50%',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '0.65rem',
                    fontWeight: 800,
                    color: '#ffffff',
                    border: '2px solid #003D66',
                  }}
                >
                  3
                </Box>
              </IconButton>

              {/* User Menu Button */}
              <Box
                onClick={handleMenuOpen}
                sx={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: 1,
                  padding: '6px 12px',
                  borderRadius: '6px',
                  backgroundColor: 'rgba(206, 17, 38, 0.2)',
                  cursor: 'pointer',
                  transition: 'all 0.3s ease',
                  '&:hover': {
                    backgroundColor: 'rgba(206, 17, 38, 0.4)',
                  },
                }}
              >
                <Avatar
                  sx={{
                    width: { xs: 32, md: 40 },
                    height: { xs: 32, md: 40 },
                    backgroundColor: '#CE1126',
                    fontWeight: 800,
                    fontSize: { xs: '0.9rem', md: '1.1rem' },
                    border: '2px solid rgba(255, 255, 255, 0.3)',
                  }}
                >
                  {user?.first_name?.[0]?.toUpperCase() || 'U'}
                </Avatar>
                <KeyboardArrowDownIcon sx={{ fontSize: '1.2rem', display: { xs: 'none', md: 'block' } }} />
              </Box>
            </Box>
          </Toolbar>
        </Container>

        {/* Notifications Menu */}
        <Menu
          anchorEl={notificationAnchor}
          open={Boolean(notificationAnchor)}
          onClose={handleNotificationClose}
          sx={{ mt: 0.5 }}
          PaperProps={{
            sx: {
              width: { xs: '280px', sm: '320px' },
              maxHeight: '400px',
              backgroundColor: '#ffffff',
              boxShadow: '0 8px 32px rgba(0, 0, 0, 0.15)',
            }
          }}
        >
          {/* Header with user info */}
          <Box sx={{ p: 2, backgroundColor: 'linear-gradient(135deg, #003D66 0%, #001f3f 100%)', color: '#ffffff' }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 800, mb: 0.5, color: '#ffffff' }}>
              {user?.first_name} {user?.last_name}
            </Typography>
            <Typography variant="caption" sx={{ opacity: 1, color: '#000000', fontWeight: 600 }}>
              {user?.email}
            </Typography>
          </Box>

          <Box sx={{ p: 1.5, borderBottom: '1px solid #e0e0e0' }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 700, color: '#003D66' }}>
              Notifications
            </Typography>
          </Box>
          <MenuItem sx={{ flexDirection: 'column', alignItems: 'flex-start', gap: 0.5, py: 1.5 }}>
            <Typography variant="body2" sx={{ fontWeight: 600 }}>
              ✅ Trajet validé
            </Typography>
            <Typography variant="caption" color="textSecondary">
              Trajet #1234 a été confirmé
            </Typography>
          </MenuItem>
          <Divider sx={{ my: 0 }} />
          <MenuItem sx={{ flexDirection: 'column', alignItems: 'flex-start', gap: 0.5, py: 1.5 }}>
            <Typography variant="body2" sx={{ fontWeight: 600 }}>
              💰 Paiement reçu
            </Typography>
            <Typography variant="caption" color="textSecondary">
              Paiement de 50 000 FCFA accepté
            </Typography>
          </MenuItem>
          <Divider sx={{ my: 0 }} />
          <MenuItem sx={{ flexDirection: 'column', alignItems: 'flex-start', gap: 0.5, py: 1.5 }}>
            <Typography variant="body2" sx={{ fontWeight: 600 }}>
              📦 Colis livré
            </Typography>
            <Typography variant="caption" color="textSecondary">
              Colis #5678 livré avec succès
            </Typography>
          </MenuItem>
          <Divider sx={{ my: 0 }} />
          <MenuItem sx={{ justifyContent: 'center', color: '#003D66', fontWeight: 600, py: 1 }}>
            Voir tout
          </MenuItem>
        </Menu>

        {/* User Menu */}
        <Menu
          anchorEl={anchorEl}
          open={Boolean(anchorEl)}
          onClose={handleMenuClose}
          sx={{ mt: 0.5 }}
          PaperProps={{
            sx: {
              minWidth: '280px',
              backgroundColor: '#ffffff',
              boxShadow: '0 8px 32px rgba(0, 0, 0, 0.15)',
            }
          }}
        >
          {/* Header with user info */}
          <Box sx={{ p: 2, backgroundColor: '#ffffff', color: '#000000', borderBottom: '2px solid #003D66' }}>
            <Typography variant="subtitle2" sx={{ fontWeight: 800, mb: 0.5, color: '#000000' }}>
              {user?.first_name} {user?.last_name}
            </Typography>
            <Typography variant="caption" sx={{ opacity: 1, color: '#000000', fontWeight: 600 }}>
              {user?.email}
            </Typography>
          </Box>

          <Divider />

          <MenuItem 
            onClick={() => { navigate('/profile'); handleMenuClose() }}
            sx={{
              py: 1.25,
              px: 2,
              '&:hover': { backgroundColor: '#f5f5f5' }
            }}
          >
            <SettingsIcon sx={{ mr: 1.5, color: '#003D66', fontSize: '1.3rem' }} />
            <Typography variant="body2" sx={{ fontWeight: 600 }}>
              Mon Profil
            </Typography>
          </MenuItem>

          <MenuItem 
            onClick={() => { navigate('/settings'); handleMenuClose() }}
            sx={{
              py: 1.25,
              px: 2,
              '&:hover': { backgroundColor: '#f5f5f5' }
            }}
          >
            <SettingsIcon sx={{ mr: 1.5, color: '#007A5E', fontSize: '1.3rem' }} />
            <Typography variant="body2" sx={{ fontWeight: 600 }}>
              Paramètres
            </Typography>
          </MenuItem>

          <Divider sx={{ my: 0.5 }} />

          <MenuItem 
            onClick={handleLogout}
            sx={{
              py: 1.25,
              px: 2,
              color: '#CE1126',
              '&:hover': { backgroundColor: '#ffebee' }
            }}
          >
            <LogoutIcon sx={{ mr: 1.5, fontSize: '1.3rem' }} />
            <Typography variant="body2" sx={{ fontWeight: 700 }}>
              Déconnexion
            </Typography>
          </MenuItem>
        </Menu>
      </AppBar>

      {/* Content Area with Sidebar */}
      <Box sx={{ display: 'flex', flex: 1 }}>
        {/* Desktop Sidebar Drawer */}
        <Drawer
          variant="permanent"
          open={openDrawer}
          sx={{
            width: openDrawer ? DRAWER_WIDTH : 0,
            flexShrink: 0,
            display: { xs: 'none', md: 'block' },
            transition: 'width 0.3s ease',
            '& .MuiDrawer-paper': {
              width: DRAWER_WIDTH,
              boxSizing: 'border-box',
              backgroundColor: '#f8f9fa',
              borderRight: '1px solid #e0e0e0',
              position: 'relative',
            },
          }}
        >
          <Box sx={{ p: 2 }}>
            <Box sx={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
              <Typography variant="overline" sx={{ fontWeight: 700, color: '#CE1126', letterSpacing: '1px' }}>
                Menu Principal
              </Typography>
              <IconButton 
                size="small" 
                onClick={handleDrawerToggle}
                sx={{ color: '#CE1126' }}
              >
                <CloseIcon fontSize="small" />
              </IconButton>
            </Box>
          </Box>

          <List>
            {visibleMenuItems.map((item) => (
              <ListItem
                key={item.path}
                onClick={() => {
                  navigate(item.path)
                }}
                sx={{
                  '&:hover': {
                    backgroundColor: 'rgba(206, 17, 38, 0.08)',
                    borderLeft: '4px solid #CE1126',
                    pl: 1.75,
                  },
                  transition: 'all 0.3s ease',
                  mb: 0.5,
                }}
              >
                <ListItemIcon sx={{ minWidth: 40, color: '#CE1126' }}>
                  {item.icon}
                </ListItemIcon>
                <ListItemText
                  primary={item.label}
                  primaryTypographyProps={{ variant: 'body2', fontWeight: 500 }}
                />
              </ListItem>
            ))}
          </List>
        </Drawer>

        {/* Mobile Sidebar Drawer */}
        <Drawer
          variant="temporary"
          open={mobileOpen}
          onClose={handleMobileDrawerToggle}
          sx={{
            display: { xs: 'block', md: 'none' },
            '& .MuiDrawer-paper': {
              width: DRAWER_WIDTH,
              boxSizing: 'border-box',
              backgroundColor: '#f8f9fa',
            },
          }}
        >
          <Box sx={{ p: 2 }}>
            <Typography variant="overline" sx={{ fontWeight: 700, color: '#CE1126', letterSpacing: '1px' }}>
              Menu Principal
            </Typography>
          </Box>

          <List>
            {visibleMenuItems.map((item) => (
              <ListItem
                key={item.path}
                onClick={() => {
                  navigate(item.path)
                  setMobileOpen(false)
                }}
                sx={{
                  '&:hover': {
                    backgroundColor: 'rgba(206, 17, 38, 0.08)',
                  },
                  transition: 'all 0.3s ease',
                  mb: 0.5,
                }}
              >
                <ListItemIcon sx={{ minWidth: 40, color: '#CE1126' }}>
                  {item.icon}
                </ListItemIcon>
                <ListItemText
                  primary={item.label}
                  primaryTypographyProps={{ variant: 'body2', fontWeight: 500 }}
                />
              </ListItem>
            ))}
          </List>

          <Divider />
          <List>
            {settingsItems.map((item) => (
              <ListItem
                key={item.path}
                onClick={() => {
                  navigate(item.path)
                  setMobileOpen(false)
                }}
                sx={{
                  '&:hover': {
                    backgroundColor: 'rgba(206, 17, 38, 0.08)',
                  },
                  transition: 'all 0.3s ease',
                }}
              >
                <ListItemIcon sx={{ minWidth: 40, color: '#007A5E' }}>
                  {item.icon}
                </ListItemIcon>
                <ListItemText
                  primary={item.label}
                  primaryTypographyProps={{ variant: 'body2', fontWeight: 500 }}
                />
              </ListItem>
            ))}
          </List>
        </Drawer>

        {/* Main Content */}
        <Box
          component="main"
          sx={{
            flexGrow: 1,
            p: 3,
            backgroundColor: '#f5f6fa',
          }}
        >
          <Container maxWidth="lg">{children}</Container>
        </Box>
      </Box>

      {/* Government Footer */}
      {!hideGovernmentHeader && <GovernmentFooter language="fr" />}
    </Box>
  )
}
