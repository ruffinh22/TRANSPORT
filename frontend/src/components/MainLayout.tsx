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
} from '@mui/icons-material'
import { useNavigate } from 'react-router-dom'
import { useAppDispatch, useAppSelector } from '../hooks'
import { logout } from '../store/authSlice'
import { GovernmentHeader } from './GovernmentHeader'
import { GovernmentFooter } from './GovernmentFooter'

const DRAWER_WIDTH = 280

interface MainLayoutProps {
  children: React.ReactNode
}

const menuItems = [
  { label: 'Tableau de bord', icon: <DashboardIcon />, path: '/dashboard' },
  { label: 'Trajets', icon: <TripsIcon />, path: '/trips' },
  { label: 'Billets', icon: <TicketsIcon />, path: '/tickets' },
  { label: 'Colis', icon: <ParcelsIcon />, path: '/parcels' },
  { label: 'Paiements', icon: <PaymentsIcon />, path: '/payments' },
  { label: 'Employés', icon: <EmployeesIcon />, path: '/employees' },
  { label: 'Villes', icon: <CitiesIcon />, path: '/cities' },
  { label: 'Rapports', icon: <ReportsIcon />, path: '/reports' },
]

const settingsItems = [
  { label: 'Paramètres', icon: <SettingsIcon />, path: '/settings' },
]

export const MainLayout: React.FC<MainLayoutProps> = ({ children }) => {
  const navigate = useNavigate()
  const dispatch = useAppDispatch()
  const { user } = useAppSelector((state) => state.auth)
  const [openDrawer, setOpenDrawer] = useState(true)
  const [mobileOpen, setMobileOpen] = useState(false)
  const [anchorEl, setAnchorEl] = useState<null | HTMLElement>(null)

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

  const handleLogout = async () => {
    await dispatch(logout())
    navigate('/login')
  }

  return (
    <Box sx={{ display: 'flex', flexDirection: 'column', minHeight: '100vh' }}>
      <CssBaseline />

      {/* Government Header */}
      <GovernmentHeader language="fr" />

      {/* App Bar */}
      <AppBar
        position="static"
        sx={{
          background: 'linear-gradient(135deg, #CE1126 0%, #007A5E 100%)',
          boxShadow: '0 2px 8px rgba(0, 0, 0, 0.1)',
        }}
      >
        <Container maxWidth="lg">
          <Toolbar disableGutters sx={{ py: 1 }}>
            <IconButton
              color="inherit"
              aria-label="toggle drawer"
              onClick={handleMobileDrawerToggle}
              sx={{ 
                mr: 2,
                display: { xs: 'flex', md: 'none' },
                backgroundColor: 'rgba(255, 255, 255, 0.2)',
                '&:hover': {
                  backgroundColor: 'rgba(255, 255, 255, 0.3)',
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
                mr: 2,
                backgroundColor: 'rgba(255, 255, 255, 0.2)',
                '&:hover': {
                  backgroundColor: 'rgba(255, 255, 255, 0.3)',
                },
              }}
            >
              <HomeIcon />
            </IconButton>

            <Typography variant="h6" component="div" sx={{ flexGrow: 1, fontWeight: 700, letterSpacing: '1px' }}>
              TKF - Gestion Transport
            </Typography>

            <Box sx={{ display: 'flex', alignItems: 'center', gap: 1 }}>
              <Avatar
                sx={{
                  width: 40,
                  height: 40,
                  bgcolor: 'rgba(255, 255, 255, 0.2)',
                  cursor: 'pointer',
                  fontWeight: 700,
                }}
                onClick={handleMenuOpen}
              >
                {user?.first_name?.[0]?.toUpperCase() || 'A'}
              </Avatar>
            </Box>

            {/* User Menu */}
            <Menu
              anchorEl={anchorEl}
              open={Boolean(anchorEl)}
              onClose={handleMenuClose}
              sx={{ mt: 1 }}
            >
              <MenuItem disabled>
                <Box>
                  <Typography variant="body2" sx={{ fontWeight: 600 }}>
                    {user?.full_name}
                  </Typography>
                  <Typography variant="caption" color="textSecondary">
                    {user?.email}
                  </Typography>
                </Box>
              </MenuItem>
              <Divider />
              <MenuItem onClick={() => { navigate('/profile'); handleMenuClose() }}>
                Profil
              </MenuItem>
              <MenuItem onClick={() => { navigate('/settings'); handleMenuClose() }}>
                Paramètres
              </MenuItem>
              <Divider />
              <MenuItem onClick={handleLogout} sx={{ color: 'error.main' }}>
                <LogoutIcon sx={{ mr: 1, fontSize: '1.2rem' }} />
                Déconnexion
              </MenuItem>
            </Menu>
          </Toolbar>
        </Container>
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
            {menuItems.map((item) => (
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
            {menuItems.map((item) => (
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
      <GovernmentFooter language="fr" />
    </Box>
  )
}
